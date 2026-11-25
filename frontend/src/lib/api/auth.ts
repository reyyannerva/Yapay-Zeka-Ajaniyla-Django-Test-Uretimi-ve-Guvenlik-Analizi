// Kimlik doğrulama servisi (H5-03 / #41) — backend/core/auth (SimpleJWT + django-axes).
import type { AuthTokens, LoginCredentials, User } from '../../types';
import { apiFetch } from './client';
import { API_TIMEOUT_MS } from './config';

/** POST /api/auth/login/ — 200 {access, refresh}; 401 hatalı bilgi; 429 kilit veya istek sınırı. */
export function login(credentials: LoginCredentials): Promise<AuthTokens> {
  return apiFetch<AuthTokens>('/api/auth/login/', {
    method: 'POST',
    auth: false,
    body: { username: credentials.username, password: credentials.password },
  });
}

/** GET /api/auth/me/ — oturumdaki kullanıcı (hassas alan içermez). */
export function getMe(signal?: AbortSignal): Promise<User> {
  return apiFetch<User>('/api/auth/me/', { signal });
}

/**
 * POST /api/auth/logout/ — refresh token'ı kara listeye alır (205). Oturum yerelde ÖNCE temizlendiği için
 * bu çağrı merkezi istemcinin yenileme akışını kullanmaz; çağıranın yakaladığı token'larla doğrudan yapılır.
 * Access süresi dolmuşsa yakalanan refresh ile bir kez yenilenip yeni refresh kara listeye alınır.
 */
export async function logoutWithTokens(tokens: { access: string | null; refresh: string | null }): Promise<void> {
  const { refresh } = tokens;
  if (!refresh) return;
  const post = (access: string | null, refreshToken: string) =>
    apiFetch<void>('/api/auth/logout/', {
      method: 'POST',
      auth: false,
      headers: access ? { Authorization: `Bearer ${access}` } : undefined,
      body: { refresh: refreshToken },
      timeoutMs: API_TIMEOUT_MS,
      // Çıkıştan hemen sonra sayfa değişse/kapansa da kara listeye alma isteği tamamlanır.
      keepalive: true,
    });
  try {
    await post(tokens.access, refresh);
  } catch (error) {
    const status = (error as { status?: number }).status;
    if (status !== 401) throw error;
    const renewed = await apiFetch<AuthTokens>('/api/auth/refresh/', {
      method: 'POST',
      auth: false,
      body: { refresh },
      keepalive: true,
    });
    await post(renewed.access, renewed.refresh ?? refresh);
  }
}

/** POST /api/auth/password-reset/ — her durumda aynı genel 200 yanıtı (hesap varlığı ifşa edilmez). */
export function requestPasswordReset(email: string): Promise<void> {
  return apiFetch<{ detail: string }>('/api/auth/password-reset/', {
    method: 'POST',
    auth: false,
    body: { email },
  }).then(() => undefined);
}

/** POST /api/auth/password-reset/confirm/ — geçersiz/süresi dolmuş/kullanılmış bağlantı 400 `token`. */
export function confirmPasswordReset(payload: { uid: string; token: string; new_password: string }): Promise<void> {
  return apiFetch<{ detail: string }>('/api/auth/password-reset/confirm/', {
    method: 'POST',
    auth: false,
    body: payload,
  }).then(() => undefined);
}
