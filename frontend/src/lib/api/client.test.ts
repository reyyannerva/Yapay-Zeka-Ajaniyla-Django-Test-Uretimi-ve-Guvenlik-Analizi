import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

import { apiFetch, isApiError, onSessionExpired, refreshAccessToken } from './client';
import { normalizeBaseUrl } from './config';
import { tokenStore } from './token-store';

// Bu dosya `fetch`'i doğrudan taklit eder (gerçek backend değil): istemcinin ortak davranışı test edilir.
type Handler = (url: string, init: RequestInit) => Response | Promise<Response>;

function json(status: number, body?: unknown, headers: Record<string, string> = {}) {
  if (body === undefined) return new Response(null, { status, headers });
  return new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json', ...headers } });
}

function route(handler: Handler) {
  const mock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => Promise.resolve(handler(String(input), init ?? {})));
  vi.stubGlobal('fetch', mock);
  return mock;
}

const callsTo = (mock: ReturnType<typeof route>, path: string) =>
  mock.mock.calls.filter(([url]) => String(url).endsWith(path));

function signedIn(access = 'eski-access', refresh = 'eski-refresh') {
  tokenStore.setTokens({ access, refresh });
}

beforeEach(() => tokenStore.clear());

afterEach(() => {
  vi.useRealTimers();
});

describe('yapılandırma', () => {
  test('API taban adresi normalize edilir', () => {
    expect(normalizeBaseUrl('https://api.ornek.test/')).toBe('https://api.ornek.test');
    expect(normalizeBaseUrl('  ')).toBe('http://localhost:8000');
    expect(normalizeBaseUrl(undefined)).toBe('http://localhost:8000');
  });
});

describe('istek ve yanıt', () => {
  beforeEach(() => signedIn('gecerli'));

  test('JSON gövde Content-Type ile, kimlik Authorization başlığıyla gönderilir; çerez gönderilmez', async () => {
    signedIn('gecerli');
    const mock = route(() => json(200, { ok: true }));
    await apiFetch('/api/x/', { method: 'POST', body: { a: 1 } });
    const [, init] = mock.mock.calls[0]!;
    const headers = new Headers(init!.headers);
    expect(headers.get('Content-Type')).toBe('application/json');
    expect(headers.get('Authorization')).toBe('Bearer gecerli');
    expect(init!.body).toBe('{"a":1}');
    expect(init!.credentials).toBe('omit');
  });

  test("FormData'da Content-Type elle yazılmaz (boundary tarayıcıya bırakılır)", async () => {
    const mock = route(() => json(201, { id: 1 }));
    const form = new FormData();
    form.append('name', 'x');
    await apiFetch('/api/projects/', { method: 'POST', body: form });
    const [, init] = mock.mock.calls[0]!;
    expect(new Headers(init!.headers).has('Content-Type')).toBe(false);
    expect(init!.body).toBe(form);
  });

  test('204 ve 205 gövdesiz yanıtlar undefined döner', async () => {
    route(() => json(204));
    await expect(apiFetch('/api/x/', { method: 'DELETE' })).resolves.toBeUndefined();
    route(() => json(205));
    await expect(apiFetch('/api/x/', { method: 'POST', auth: false })).resolves.toBeUndefined();
  });

  test('boş dizi (boş sonuç) hata sayılmaz', async () => {
    route(() => json(200, []));
    await expect(apiFetch('/api/x/')).resolves.toEqual([]);
  });

  test('400 alan hataları olduğu gibi iletilir', async () => {
    route(() => json(400, { name: ['Bu alan zorunlu.'] }));
    await expect(apiFetch('/api/x/', { method: 'POST', body: {} })).rejects.toEqual({ status: 400, body: { name: ['Bu alan zorunlu.'] } });
  });

  test.each([403, 404])('%i hatası yenileme tetiklemez', async (status) => {
    signedIn();
    const mock = route(() => json(status, { detail: 'yok' }));
    await expect(apiFetch('/api/x/')).rejects.toMatchObject({ status });
    expect(callsTo(mock, '/api/auth/refresh/')).toHaveLength(0);
    expect(tokenStore.getAccess()).toBe('eski-access');
  });

  test('500 yanıtındaki sunucu ayrıntısı (HTML/stack trace) kullanıcıya iletilmez', async () => {
    route(() => new Response('<html>Traceback (most recent call last) SECRET</html>', { status: 500, headers: { 'content-type': 'text/html' } }));
    const error = await apiFetch('/api/x/').catch((e: unknown) => e);
    expect(isApiError(error) && error.status).toBe(500);
    expect(JSON.stringify(error)).not.toContain('Traceback');
    expect(JSON.stringify(error)).toContain('beklenmeyen bir hata');
  });

  test('ağ hatası status 0 / network_error olarak normalize edilir', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new TypeError('Failed to fetch'))));
    await expect(apiFetch('/api/x/')).rejects.toMatchObject({ status: 0, body: { code: 'network_error' } });
  });

  test('zaman aşımı status 0 / timeout olarak normalize edilir ve istek iptal edilir', async () => {
    let aborted = false;
    vi.stubGlobal(
      'fetch',
      vi.fn(
        (_url: string, init: RequestInit) =>
          new Promise((_resolve, reject) => {
            init.signal!.addEventListener('abort', () => {
              aborted = true;
              reject(new DOMException('Aborted', 'AbortError'));
            });
          }),
      ),
    );
    await expect(apiFetch('/api/x/', { timeoutMs: 20 })).rejects.toMatchObject({ status: 0, body: { code: 'timeout' } });
    expect(aborted).toBe(true);
  });

  test('çağıranın iptali (AbortSignal) hata mesajına çevrilmeden iletilir', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(
        (_url: string, init: RequestInit) =>
          new Promise((_resolve, reject) => {
            init.signal!.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')));
          }),
      ),
    );
    const controller = new AbortController();
    const pending = apiFetch('/api/x/', { signal: controller.signal });
    controller.abort();
    await expect(pending).rejects.toMatchObject({ name: 'AbortError' });
  });
});

describe('access token yenileme', () => {
  test('401 sonrası tek yenileme yapılır, yeni token (rotasyon) saklanır ve istek bir kez yinelenir', async () => {
    signedIn();
    const mock = route((url, init) => {
      if (url.endsWith('/api/auth/refresh/')) return json(200, { access: 'yeni-access', refresh: 'yeni-refresh' });
      const auth = new Headers(init.headers).get('Authorization');
      return auth === 'Bearer yeni-access' ? json(200, { id: 1 }) : json(401, { detail: 'süresi doldu', code: 'token_not_valid' });
    });
    await expect(apiFetch('/api/projects/1/')).resolves.toEqual({ id: 1 });
    expect(callsTo(mock, '/api/auth/refresh/')).toHaveLength(1);
    expect(JSON.parse(String(callsTo(mock, '/api/auth/refresh/')[0]![1]!.body))).toEqual({ refresh: 'eski-refresh' });
    expect(callsTo(mock, '/api/projects/1/')).toHaveLength(2);
    expect(tokenStore.getAccess()).toBe('yeni-access');
    expect(tokenStore.getRefresh()).toBe('yeni-refresh');
  });

  test('eş zamanlı 401 yanıtları tek bir yenileme isteğini paylaşır', async () => {
    signedIn();
    let resolveRefresh!: (r: Response) => void;
    const mock = route((url, init) => {
      if (url.endsWith('/api/auth/refresh/')) return new Promise<Response>((r) => (resolveRefresh = r));
      const auth = new Headers(init.headers).get('Authorization');
      return auth === 'Bearer yeni-access' ? json(200, { url }) : json(401, { detail: 'x' });
    });
    const requests = [apiFetch('/api/a/'), apiFetch('/api/b/'), apiFetch('/api/c/')];
    await vi.waitFor(() => expect(callsTo(mock, '/api/auth/refresh/')).toHaveLength(1));
    resolveRefresh(json(200, { access: 'yeni-access', refresh: 'yeni-refresh' }));
    await expect(Promise.all(requests)).resolves.toHaveLength(3);
    expect(callsTo(mock, '/api/auth/refresh/')).toHaveLength(1);
  });

  test('refresh 401 ise oturum sonlandırılır, sonsuz döngü oluşmaz', async () => {
    signedIn();
    const expired = vi.fn();
    const unsubscribe = onSessionExpired(expired);
    const mock = route(() => json(401, { detail: 'Token is blacklisted', code: 'token_not_valid' }));
    await expect(apiFetch('/api/projects/')).rejects.toMatchObject({ status: 401 });
    expect(callsTo(mock, '/api/auth/refresh/')).toHaveLength(1);
    expect(callsTo(mock, '/api/projects/')).toHaveLength(1);
    expect(expired).toHaveBeenCalledTimes(1);
    expect(tokenStore.hasSession()).toBe(false);
    unsubscribe();
  });

  test('yenilenmiş token ile tekrar 401 gelirse yeniden yenileme yapılmaz (en fazla bir yineleme)', async () => {
    signedIn();
    const mock = route((url) =>
      url.endsWith('/api/auth/refresh/') ? json(200, { access: 'yeni-access', refresh: 'yeni-refresh' }) : json(401, { detail: 'x' }),
    );
    await expect(apiFetch('/api/x/')).rejects.toMatchObject({ status: 401 });
    expect(callsTo(mock, '/api/auth/refresh/')).toHaveLength(1);
    expect(callsTo(mock, '/api/x/')).toHaveLength(2);
    expect(tokenStore.hasSession()).toBe(false);
  });

  test('yenileme sırasında ağ hatası oturumu sonlandırmaz', async () => {
    signedIn();
    const expired = vi.fn();
    const unsubscribe = onSessionExpired(expired);
    vi.stubGlobal(
      'fetch',
      vi.fn((url: string) => (url.endsWith('/api/auth/refresh/') ? Promise.reject(new TypeError('offline')) : Promise.resolve(json(401, { detail: 'x' })))),
    );
    await expect(apiFetch('/api/x/')).rejects.toMatchObject({ status: 0, body: { code: 'network_error' } });
    expect(expired).not.toHaveBeenCalled();
    expect(tokenStore.getRefresh()).toBe('eski-refresh');
    unsubscribe();
  });

  test('yenileme sürerken çıkış yapılırsa geç gelen yanıt oturumu geri getirmez', async () => {
    signedIn();
    let resolveRefresh!: (r: Response) => void;
    route((url) => (url.endsWith('/api/auth/refresh/') ? new Promise<Response>((r) => (resolveRefresh = r)) : json(401, {})));
    const outcome = refreshAccessToken();
    tokenStore.clear(); // çıkış
    resolveRefresh(json(200, { access: 'gec-access', refresh: 'gec-refresh' }));
    await expect(outcome).resolves.toBe('invalid');
    expect(tokenStore.getAccess()).toBeNull();
    expect(tokenStore.getRefresh()).toBeNull();
  });

  test('sayfa yenilemesinden sonra (yalnızca refresh token) önce access alınır', async () => {
    window.sessionStorage.setItem('testkalkan.refresh', 'saklanan');
    const mock = route((url, init) => {
      if (url.endsWith('/api/auth/refresh/')) return json(200, { access: 'a2', refresh: 'r2' });
      return json(200, { auth: new Headers(init.headers).get('Authorization') });
    });
    await expect(apiFetch('/api/auth/me/')).resolves.toEqual({ auth: 'Bearer a2' });
    expect(mock.mock.calls.map(([u]) => String(u).replace(/^.*\/api/, '/api'))).toEqual(['/api/auth/refresh/', '/api/auth/me/']);
  });

  test('oturum yokken kimlik gerektiren istek gönderilmez (401), kimliksiz uçlar çalışır', async () => {
    const mock = route(() => json(200, {}));
    await expect(apiFetch('/api/projects/')).rejects.toMatchObject({ status: 401, body: { code: 'not_authenticated' } });
    expect(mock).not.toHaveBeenCalled();
    await expect(apiFetch('/api/auth/password-reset/', { method: 'POST', auth: false, body: { email: 'a@b.test' } })).resolves.toEqual({});
  });

  test("token'lar URL'ye yazılmaz", async () => {
    signedIn('gizli-access', 'gizli-refresh');
    const mock = route(() => json(200, {}));
    await apiFetch('/api/projects/?page=1');
    expect(String(mock.mock.calls[0]![0])).not.toMatch(/gizli/);
  });
});
