import type { ApiError, AuthTokens, LoginCredentials, User } from '../../types';

// Mock: gerçek HTTP çağrısı #41'de. Değerler açıkça örnektir.
const MOCK_USER: User = { id: 1, username: 'ornek-kullanici', email: 'ornek@example.test' };

// --- Mock senaryo sabitleri (yalnızca geliştirme/test; gerçek API'de karşılığı yoktur) ---
/** Bu parola "yanlış" sayılır: 1-2. deneme 401, 3. deneme 429 (hesap kilidi, docs/api/authentication.md). */
export const MOCK_WRONG_PASSWORD = 'yanlis-parola';
/** Şifre sıfırlama onayında bu token "geçersiz/süresi dolmuş/kullanılmış" sayılır (400 `token`). */
export const MOCK_INVALID_RESET_TOKEN = 'gecersiz-token';
const MOCK_MIN_PASSWORD_LENGTH = 8;
const MOCK_LOCK_AFTER_ATTEMPTS = 3;

// Kilit yanıtında Retry-After / kalan süre alanı yoktur; arayüz süre uydurmaz.
const LOCK_DETAIL =
  'Çok fazla başarısız giriş denemesi. Hesap geçici olarak kilitlendi; lütfen bir süre sonra tekrar deneyin.';

let failedAttempts = 0;

/** Testler/geliştirme için başarısız deneme sayacını sıfırlar. */
export function resetMockLoginAttempts(): void {
  failedAttempts = 0;
}

function apiError(status: ApiError['status'], body: ApiError['body']): ApiError {
  return { status, body };
}

export function login(credentials: LoginCredentials): Promise<AuthTokens> {
  if (failedAttempts >= MOCK_LOCK_AFTER_ATTEMPTS) {
    return Promise.reject(apiError(429, { detail: LOCK_DETAIL }));
  }
  if (credentials.password === MOCK_WRONG_PASSWORD) {
    failedAttempts += 1;
    if (failedAttempts >= MOCK_LOCK_AFTER_ATTEMPTS) {
      return Promise.reject(apiError(429, { detail: LOCK_DETAIL }));
    }
    // Kullanıcı adı / parola yanlışı aynı yanıtı verir.
    return Promise.reject(apiError(401, { detail: 'Kullanıcı adı veya parola hatalı.' }));
  }
  failedAttempts = 0;
  return Promise.resolve({ access: 'ornek-access-token', refresh: 'ornek-refresh-token' });
}

export function logout(): Promise<void> {
  return Promise.resolve();
}

export function getMe(): Promise<User> {
  return Promise.resolve({ ...MOCK_USER });
}

export function requestPasswordReset(email: string): Promise<void> {
  // Kayıtlı/kayıtsız her zaman 200; yalnızca geçersiz e-posta biçimi 400.
  if (!email.includes('@')) {
    return Promise.reject(apiError(400, { email: ['Geçerli bir e-posta adresi girin.'] }));
  }
  return Promise.resolve();
}

export function confirmPasswordReset(payload: {
  uid: string;
  token: string;
  new_password: string;
}): Promise<void> {
  if (payload.token === MOCK_INVALID_RESET_TOKEN) {
    return Promise.reject(
      apiError(400, { token: ['Bağlantı geçersiz, süresi dolmuş veya daha önce kullanılmış.'] }),
    );
  }
  if (payload.new_password.length < MOCK_MIN_PASSWORD_LENGTH) {
    return Promise.reject(
      apiError(400, {
        new_password: [`Bu parola çok kısa. En az ${MOCK_MIN_PASSWORD_LENGTH} karakter olmalı.`],
      }),
    );
  }
  return Promise.resolve();
}
