// Ortak HTTP istemcisi (H5-03 / #41): tüm servisler yalnızca `apiFetch` üzerinden Django/DRF API'sine gider.
// - Taban adres VITE_API_BASE_URL'den okunur; ekranlarda adres yazılmaz.
// - JSON ve multipart/form-data (FormData: Content-Type ve boundary tarayıcıya bırakılır) desteklenir.
// - 204/205 gövdesiz yanıtlar `undefined` döner.
// - Hatalar `ApiError { status, body }` biçimine normalize edilir; bağlantı hatası ve zaman aşımı status 0.
// - 401'de tek seferlik (single-flight) refresh yapılır ve istek EN FAZLA bir kez yinelenir. DRF kimlik
//   doğrulaması görünüm mantığından önce çalıştığından 401 alan bir istek sunucuda yan etki üretmemiştir;
//   bu nedenle yan etkili isteklerin tek yinelemesi çift kayıt oluşturmaz. 403 asla yenileme tetiklemez.

import type { ApiError, AuthTokens } from '../../types';
import { API_BASE_URL, API_TIMEOUT_MS } from './config';
import { tokenStore } from './token-store';

export interface ApiFetchInit extends Omit<RequestInit, 'body'> {
  /** JSON gövde (nesne) veya multipart için FormData. */
  body?: FormData | Record<string, unknown> | unknown[] | null;
  /** false: Authorization eklenmez ve 401'de yenileme yapılmaz (giriş, sıfırlama, yenileme uçları). */
  auth?: boolean;
  timeoutMs?: number;
}

/** Servis katmanındaki reddedilen hata değerinin ApiError olup olmadığını söyler. */
export function isApiError(value: unknown): value is ApiError {
  return (
    typeof value === 'object' &&
    value !== null &&
    'status' in value &&
    typeof (value as { status: unknown }).status === 'number' &&
    'body' in value
  );
}

export const NETWORK_ERROR_DETAIL = 'Sunucuya bağlanılamadı. İnternet bağlantınızı veya sunucunun çalıştığını kontrol edin.';
export const TIMEOUT_DETAIL = 'İstek zaman aşımına uğradı. Lütfen tekrar deneyin.';
export const SERVER_ERROR_DETAIL = 'Sunucuda beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin.';

function networkError(): ApiError {
  return { status: 0, body: { detail: NETWORK_ERROR_DETAIL, code: 'network_error' } };
}

function timeoutError(): ApiError {
  return { status: 0, body: { detail: TIMEOUT_DETAIL, code: 'timeout' } };
}

// --- Oturum sonu bildirimi (refresh token geçersiz/süresi dolmuş) ---
type ExpiredListener = () => void;
const expiredListeners = new Set<ExpiredListener>();

export function onSessionExpired(listener: ExpiredListener): () => void {
  expiredListeners.add(listener);
  return () => {
    expiredListeners.delete(listener);
  };
}

function notifyExpired(): void {
  expiredListeners.forEach((listener) => listener());
}

// --- Düşük seviyeli istek ---
function buildUrl(path: string): string {
  if (!path.startsWith('/')) throw new Error('API yolu "/" ile başlamalıdır.');
  return `${API_BASE_URL}${path}`;
}

async function parseBody(response: Response): Promise<unknown> {
  if (response.status === 204 || response.status === 205) return undefined;
  const text = await response.text();
  if (!text) return undefined;
  const type = response.headers.get('content-type') ?? '';
  if (type.includes('json')) {
    try {
      return JSON.parse(text) as unknown;
    } catch {
      return undefined;
    }
  }
  return undefined; // HTML hata sayfaları vb. kullanıcıya iletilmez
}

function toApiError(status: number, body: unknown): ApiError {
  if (status >= 500) {
    // Stack trace veya sunucu ayrıntısı gösterilmez.
    return { status, body: { detail: SERVER_ERROR_DETAIL } };
  }
  if (body && typeof body === 'object') return { status, body: body as ApiError['body'] };
  return { status, body: { detail: `İstek başarısız oldu (HTTP ${status}).` } };
}

interface RawResult {
  response: Response;
  body: unknown;
}

async function rawRequest(path: string, init: ApiFetchInit, accessToken: string | null): Promise<RawResult> {
  const { body, auth: _auth, timeoutMs = API_TIMEOUT_MS, headers, signal, ...rest } = init;
  const finalHeaders = new Headers(headers);
  finalHeaders.set('Accept', 'application/json');
  let payload: BodyInit | undefined;
  if (body instanceof FormData) {
    payload = body; // Content-Type (boundary dahil) tarayıcı tarafından üretilir
  } else if (body !== undefined && body !== null) {
    finalHeaders.set('Content-Type', 'application/json');
    payload = JSON.stringify(body);
  }
  if (accessToken) finalHeaders.set('Authorization', `Bearer ${accessToken}`);

  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);
  const onExternalAbort = () => controller.abort();
  if (signal) {
    if (signal.aborted) controller.abort();
    else signal.addEventListener('abort', onExternalAbort, { once: true });
  }
  try {
    const response = await fetch(buildUrl(path), {
      ...rest,
      headers: finalHeaders,
      body: payload,
      signal: controller.signal,
      credentials: 'omit', // kimlik doğrulama yalnızca Authorization başlığıyla; çerez gönderilmez
    });
    return { response, body: await parseBody(response) };
  } catch (error) {
    if (timedOut) throw timeoutError();
    if (signal?.aborted) throw error; // çağıran iptal etti (ör. sorgu iptali): olduğu gibi iletilir
    throw networkError();
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', onExternalAbort);
  }
}

// --- Access token yenileme (single-flight) ---
export type RefreshOutcome = 'refreshed' | 'invalid' | 'network';
let refreshInFlight: Promise<RefreshOutcome> | null = null;

/**
 * Saklanan refresh token ile yeni access (ve rotasyonla yeni refresh) alır. Eş zamanlı çağrılar aynı
 * isteği paylaşır. Refresh geçersizse oturum temizlenir ve dinleyicilere bildirilir; ağ hatasında oturum
 * korunur. Çıkış (generation değişimi) sonrası gelen yanıt yok sayılır.
 */
export function refreshAccessToken(): Promise<RefreshOutcome> {
  if (refreshInFlight) return refreshInFlight;
  const refresh = tokenStore.getRefresh();
  if (!refresh) return Promise.resolve('invalid');
  const generation = tokenStore.generation();
  refreshInFlight = rawRequest('/api/auth/refresh/', { method: 'POST', body: { refresh } }, null)
    .then(({ response, body }): RefreshOutcome => {
      if (generation !== tokenStore.generation()) return 'invalid';
      if (response.ok && body && typeof body === 'object' && 'access' in body) {
        tokenStore.setTokens(body as AuthTokens);
        return 'refreshed';
      }
      if (response.status >= 500) return 'network';
      tokenStore.clear();
      notifyExpired();
      return 'invalid';
    })
    .catch((): RefreshOutcome => 'network')
    .finally(() => {
      refreshInFlight = null;
    });
  return refreshInFlight;
}

/** Ortak istek. Başarılı yanıt gövdesini döndürür; hata durumunda ApiError fırlatır. */
export async function apiFetch<T>(path: string, init: ApiFetchInit = {}): Promise<T> {
  const useAuth = init.auth !== false;
  let access = useAuth ? tokenStore.getAccess() : null;

  // Sayfa yenilemesinden sonra yalnızca refresh token varsa önce access alınır.
  if (useAuth && !access && tokenStore.getRefresh()) {
    const outcome = await refreshAccessToken();
    if (outcome === 'network') throw networkError();
    if (outcome === 'invalid') {
      // Oturum sona erdi (dinleyiciler bilgilendirildi); kimliksiz istek boşuna gönderilmez.
      throw { status: 401, body: { detail: 'Oturum süresi doldu.', code: 'session_expired' } } satisfies ApiError;
    }
    access = tokenStore.getAccess();
  }

  if (useAuth && !access) {
    // Oturum yok (ör. çıkıştan sonra tamamlanan bir isteğin tetiklediği yeniden çekme): kimliksiz istek gönderilmez.
    throw { status: 401, body: { detail: 'Oturum açık değil.', code: 'not_authenticated' } } satisfies ApiError;
  }

  let result = await rawRequest(path, init, access);

  if (useAuth && result.response.status === 401 && tokenStore.getRefresh()) {
    const outcome = await refreshAccessToken();
    if (outcome === 'refreshed') {
      result = await rawRequest(path, init, tokenStore.getAccess()); // en fazla bir yineleme
    } else if (outcome === 'network') {
      throw networkError();
    }
  }

  if (!result.response.ok) {
    if (useAuth && result.response.status === 401) {
      // Yenileme mümkün değil: oturum gerçekten sona erdi.
      if (tokenStore.hasSession()) {
        tokenStore.clear();
        notifyExpired();
      }
    }
    throw toApiError(result.response.status, result.body);
  }
  return result.body as T;
}

/** Testler için: devam eden yenileme durumunu sıfırlar. */
export function __resetClientStateForTests(): void {
  refreshInFlight = null;
  expiredListeners.clear();
}
