import type { AuthTokens, LoginCredentials, User } from '../../types';

// Mock: gerçek HTTP çağrısı #41'de. Değerler açıkça örnektir.
const MOCK_USER: User = { id: 1, username: 'ornek-kullanici', email: 'ornek@example.test' };

export function login(_c: LoginCredentials): Promise<AuthTokens> {
  return Promise.resolve({ access: 'ornek-access-token', refresh: 'ornek-refresh-token' });
}

export function logout(): Promise<void> {
  return Promise.resolve();
}

export function getMe(): Promise<User> {
  return Promise.resolve({ ...MOCK_USER });
}

export function requestPasswordReset(_email: string): Promise<void> {
  return Promise.resolve();
}

export function confirmPasswordReset(_p: {
  uid: string;
  token: string;
  new_password: string;
}): Promise<void> {
  return Promise.resolve();
}
