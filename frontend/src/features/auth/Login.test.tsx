import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';

import { ToastProvider } from '../../components/ui/Toast';
import { tokenStore } from '../../lib/api/token-store';
import { AuthProvider } from '../../lib/auth-context';
import { ThemeProvider } from '../../lib/theme-context';
import { MOCK_WRONG_PASSWORD, fakeCalls } from '../../test/fake-api';
import { ROUTER_FUTURE } from '../../test/router-future';
import { Login } from './Login';

// Anonim başlangıç: varsayılan test oturumu temizlenir.
beforeEach(() => tokenStore.clear());

// Sahte HTTP backend (src/test/fake-api.ts): "yanlis-parola" yanlış sayılır (1-2. deneme 401, 3. deneme 429).
const WRONG = { username: 'ornek-kullanici', password: MOCK_WRONG_PASSWORD };
const RIGHT = { username: 'ornek-kullanici', password: 'dogru-parola-ornek' };

function renderLogin() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <ThemeProvider>
      <ToastProvider>
        <QueryClientProvider client={client}>
          <AuthProvider>
            <MemoryRouter initialEntries={['/login']} future={ROUTER_FUTURE}>
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/dashboard" element={<div data-testid="dashboard-route" />} />
              </Routes>
            </MemoryRouter>
          </AuthProvider>
        </QueryClientProvider>
      </ToastProvider>
    </ThemeProvider>,
  );
}

async function submit(creds: { username: string; password: string }) {
  await userEvent.clear(screen.getByLabelText(/Kullanıcı adı/));
  await userEvent.clear(screen.getByLabelText(/Parola/));
  await userEvent.type(screen.getByLabelText(/Kullanıcı adı/), creds.username);
  await userEvent.type(screen.getByLabelText(/Parola/), creds.password);
  await userEvent.click(screen.getByRole('button', { name: /Giriş/ }));
}

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });
}

test('boş form zorunlu alan hatası gösterir ve istek gönderilmez', async () => {
  renderLogin();
  await userEvent.click(screen.getByRole('button', { name: /Giriş/ }));
  expect(await screen.findByText(/Kullanıcı adı zorunludur/)).toBeInTheDocument();
  expect(fakeCalls().some((c) => c.path === '/api/auth/login/')).toBe(false);
});

test('1. hatalı denemede kimlik hatası gösterilir, kilit uyarısı gösterilmez', async () => {
  renderLogin();
  await submit(WRONG);
  expect(await screen.findByRole('alert')).toHaveTextContent('Kullanıcı adı veya parola hatalı.');
  expect(screen.queryByText(/kilitlendi/i)).not.toBeInTheDocument();
});

test('3. hatalı denemede sunucunun kilit yanıtı ve sunucunun bildirdiği kalan süre gösterilir', async () => {
  renderLogin();
  await submit(WRONG);
  await submit(WRONG);
  expect(screen.queryByText(/geçici olarak kilitlendi/i)).not.toBeInTheDocument();
  await submit(WRONG);
  expect(await screen.findByText('Hesap kilitlendi')).toBeInTheDocument();
  expect(screen.getByText(/15 dk kilitlenir/)).toBeInTheDocument();
  // fake-api retry_after_seconds: 900 → 15 dk 00 sn (veya saniye ilerlediyse 14 dk ..)
  expect(screen.getByTestId('lock-remaining')).toHaveTextContent(/1[45] dk \d{2} sn/);
});

test('kilit süresinde doğru parola da reddedilir; token saklanmaz', async () => {
  renderLogin();
  for (let i = 0; i < 3; i += 1) await submit(WRONG);
  await submit(RIGHT);
  expect(await screen.findByText('Hesap kilitlendi')).toBeInTheDocument();
  expect(screen.queryByTestId('dashboard-route')).not.toBeInTheDocument();
  expect(tokenStore.hasSession()).toBe(false);
});

test('sunucu kalan süre bildirmezse geri sayım uydurulmaz', async () => {
  vi.mocked(fetch).mockResolvedValueOnce(
    jsonResponse(429, { detail: 'Kilit', code: 'account_locked', locked_until: null, retry_after_seconds: null }),
  );
  renderLogin();
  await submit(RIGHT);
  expect(await screen.findByText('Hesap kilitlendi')).toBeInTheDocument();
  expect(screen.queryByTestId('lock-remaining')).not.toBeInTheDocument();
});

test('istek sınırı 429 (code yok) hesap kilidi olarak gösterilmez', async () => {
  vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(429, { detail: 'İstek sınırlandı.' }));
  renderLogin();
  await submit(RIGHT);
  expect(await screen.findByRole('alert')).toHaveTextContent(/çok fazla giriş isteği/);
  expect(screen.queryByText('Hesap kilitlendi')).not.toBeInTheDocument();
});

test('bağlantı hatası yanlış parola ile karıştırılmaz', async () => {
  vi.mocked(fetch).mockRejectedValueOnce(new TypeError('Failed to fetch'));
  renderLogin();
  await submit(RIGHT);
  expect(await screen.findByRole('alert')).toHaveTextContent(/Sunucuya bağlanılamadı/);
  expect(screen.queryByText(/parola hatalı/)).not.toBeInTheDocument();
});

test('form "Kullanıcı adı" alanını backend `username` alanına gönderir', async () => {
  renderLogin();
  await submit(RIGHT);
  await screen.findByTestId('dashboard-route');
  const call = fakeCalls().find((c) => c.path === '/api/auth/login/');
  expect(JSON.parse(String(call?.body))).toEqual({ username: 'ornek-kullanici', password: RIGHT.password });
});

test("başarılı girişte gerçek token'lar saklanır, kullanıcı doğrulanır ve /dashboard'a yönlenir", async () => {
  renderLogin();
  await submit(RIGHT);
  expect(await screen.findByTestId('dashboard-route')).toBeInTheDocument();
  expect(tokenStore.getAccess()).toBe('test-access');
  expect(window.sessionStorage.getItem('testkalkan.refresh')).toBe('test-refresh');
  const me = fakeCalls().find((c) => c.path === '/api/auth/me/');
  expect(me?.headers.get('Authorization')).toBe('Bearer test-access');
});
