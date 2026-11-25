import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

import { fakeCalls } from '../test/fake-api';
import { tokenStore } from './api/token-store';
import { AuthProvider, useAuth } from './auth-context';
import type { AuthContextValue } from './auth-context';

// Anonim başlangıç: varsayılan test oturumu temizlenir.
beforeEach(() => tokenStore.clear());

let auth: AuthContextValue;
function Probe() {
  auth = useAuth();
  return <span data-testid="status">{`${auth.status}:${auth.user?.username ?? '-'}`}</span>;
}

function renderAuth(client: QueryClient) {
  return render(
    <QueryClientProvider client={client}>
      <AuthProvider>
        <Probe />
      </AuthProvider>
    </QueryClientProvider>,
  );
}

test('giriş: gerçek token alınır, /me ile doğrulanır; önceki önbellek temizlenir', async () => {
  const client = new QueryClient();
  client.setQueryData(['projects', 'list', {}], { results: [{ id: 99, name: 'Önceki kullanıcının projesi' }] });
  renderAuth(client);
  expect(screen.getByTestId('status')).toHaveTextContent('anonymous:-');
  await act(() => auth.signIn({ username: 'ornek-kullanici', password: 'dogru' }));
  expect(screen.getByTestId('status')).toHaveTextContent('authenticated:ornek-kullanici');
  expect(client.getQueryData(['projects', 'list', {}])).toBeUndefined();
});

test('çıkış: önbellek ve token temizlenir, refresh token sunucuda kara listeye alınır', async () => {
  const client = new QueryClient();
  renderAuth(client);
  await act(() => auth.signIn({ username: 'ornek-kullanici', password: 'dogru' }));
  client.setQueryData(['projects', 'detail', 1], { id: 1, name: 'Gizli proje' });

  act(() => auth.signOut());
  expect(screen.getByTestId('status')).toHaveTextContent('anonymous:-');
  expect(client.getQueryData(['projects', 'detail', 1])).toBeUndefined();
  expect(tokenStore.hasSession()).toBe(false);
  await waitFor(() => expect(fakeCalls().some((c) => c.path === '/api/auth/logout/')).toBe(true));
  const logout = fakeCalls().find((c) => c.path === '/api/auth/logout/')!;
  expect(JSON.parse(String(logout.body))).toEqual({ refresh: 'test-refresh' });
  expect(logout.headers.get('Authorization')).toBe('Bearer test-access');
});

test('çıkış isteği başarısız olsa da yerel oturum kapanır', async () => {
  const client = new QueryClient();
  renderAuth(client);
  await act(() => auth.signIn({ username: 'ornek-kullanici', password: 'dogru' }));
  vi.mocked(fetch).mockRejectedValueOnce(new TypeError('offline'));
  act(() => auth.signOut());
  expect(screen.getByTestId('status')).toHaveTextContent('anonymous:-');
  expect(tokenStore.hasSession()).toBe(false);
});

test('access süresi dolmuşsa çıkışta bir kez yenilenip YENİ refresh token kara listeye alınır', async () => {
  const client = new QueryClient();
  renderAuth(client);
  await act(() => auth.signIn({ username: 'ornek-kullanici', password: 'dogru' }));
  vi.mocked(fetch).mockResolvedValueOnce(
    new Response(JSON.stringify({ detail: 'expired', code: 'token_not_valid' }), {
      status: 401,
      headers: { 'content-type': 'application/json' },
    }),
  );
  act(() => auth.signOut());
  await waitFor(() => expect(fakeCalls().filter((c) => c.path === '/api/auth/logout/')).toHaveLength(1));
  // İlk logout taklit 401 aldı (fakeCalls'a düşmedi); ardından refresh ve yeni refresh ile logout.
  expect(fakeCalls().some((c) => c.path === '/api/auth/refresh/')).toBe(true);
  const logout = fakeCalls().find((c) => c.path === '/api/auth/logout/')!;
  expect(JSON.parse(String(logout.body))).toEqual({ refresh: 'test-refresh-2' });
  expect(tokenStore.hasSession()).toBe(false);
});

test('kullanıcı değişiminde önceki kullanıcının verisi önbellekte kalmaz', async () => {
  const client = new QueryClient();
  renderAuth(client);
  await act(() => auth.signIn({ username: 'kullanici-a', password: 'dogru' }));
  client.setQueryData(['projects', 'list', {}], { results: [{ id: 1, name: 'A projesi' }] });
  act(() => auth.signOut());
  await act(() => auth.signIn({ username: 'kullanici-b', password: 'dogru' }));
  expect(client.getQueryData(['projects', 'list', {}])).toBeUndefined();
});

test('refresh token geçersizleşince oturum "süresi doldu" durumuna geçer ve önbellek temizlenir', async () => {
  const client = new QueryClient();
  renderAuth(client);
  await act(() => auth.signIn({ username: 'ornek-kullanici', password: 'dogru' }));
  client.setQueryData(['projects', 'detail', 1], { id: 1 });
  // access reddedilir, refresh de kara listede: merkezi istemci oturumu sonlandırır.
  const unauthorized = () =>
    new Response(JSON.stringify({ detail: 'x', code: 'token_not_valid' }), { status: 401, headers: { 'content-type': 'application/json' } });
  vi.mocked(fetch).mockResolvedValueOnce(unauthorized()).mockResolvedValueOnce(unauthorized());
  const { getProject } = await import('./api/projects');
  let failure: unknown;
  await act(async () => {
    failure = await getProject(1).catch((e: unknown) => e);
  });
  expect(failure).toMatchObject({ status: 401 });
  await waitFor(() => expect(auth.sessionExpired).toBe(true));
  expect(screen.getByTestId('status')).toHaveTextContent('anonymous:-');
  expect(client.getQueryData(['projects', 'detail', 1])).toBeUndefined();
});
