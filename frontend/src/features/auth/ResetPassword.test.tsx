import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { expect, test, vi } from 'vitest';

import { ToastProvider } from '../../components/ui/Toast';
import { ThemeProvider } from '../../lib/theme-context';
import { fakeCalls } from '../../test/fake-api';
import { ROUTER_FUTURE } from '../../test/router-future';
import { ResetPassword } from './ResetPassword';

function renderReset(search: string) {
  return render(
    <ThemeProvider>
    <ToastProvider>
      <MemoryRouter initialEntries={[`/reset-password${search}`]} future={ROUTER_FUTURE}>
        <Routes>
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/login" element={<div data-testid="login-route" />} />
        </Routes>
      </MemoryRouter>
    </ToastProvider>
    </ThemeProvider>,
  );
}

async function fill(password: string, confirm: string) {
  await userEvent.type(screen.getByLabelText(/^Yeni parola/), password);
  await userEvent.type(screen.getByLabelText(/Parola \(tekrar\)/), confirm);
  await userEvent.click(screen.getByRole('button', { name: /Parolayı güncelle/ }));
}

test('uid/token query parametreleri yoksa geçersiz bağlantı mesajı gösterilir', () => {
  renderReset('');
  expect(screen.getByText(/geçersiz|süresi dolmuş/i)).toBeInTheDocument();
  expect(screen.queryByLabelText(/^Yeni parola/)).not.toBeInTheDocument();
});

test("uid/token query'den okunur; geçerli parola ile /login'e yönlenir", async () => {
  renderReset('?uid=ornek-uid&token=ornek-token');
  await fill('yeni-parola-ornek', 'yeni-parola-ornek');
  expect(await screen.findByTestId('login-route')).toBeInTheDocument();
});

test('parolalar eşleşmezse hata gösterilir', async () => {
  renderReset('?uid=ornek-uid&token=ornek-token');
  await fill('yeni-parola-ornek', 'baska-parola-ornek');
  expect(await screen.findByText(/eşleşmiyor/i)).toBeInTheDocument();
});

test('geçersiz/süresi dolmuş token (400 token) hatası gösterilir', async () => {
  renderReset('?uid=ornek-uid&token=gecersiz-token');
  await fill('yeni-parola-ornek', 'yeni-parola-ornek');
  expect(await screen.findByRole('alert')).toHaveTextContent(/geçersiz|süresi dolmuş|kullanılmış/i);
});

test('zayıf parola (400 new_password) alan hatası olarak gösterilir', async () => {
  renderReset('?uid=ornek-uid&token=ornek-token');
  await fill('kisa', 'kisa');
  expect(await screen.findByText(/çok kısa/i)).toBeInTheDocument();
});

// --- H5-03 / #41 ---
test('bağlantıdaki uid/token okunduktan sonra adres çubuğundan silinir; gönderimde yine kullanılır', async () => {
  function Location() {
    return <span data-testid="search">{useLocation().search}</span>;
  }
  render(
    <ThemeProvider>
      <ToastProvider>
        <MemoryRouter initialEntries={['/reset-password?uid=MQ&token=gizli-token']} future={ROUTER_FUTURE}>
          <Location />
          <Routes>
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route path="/login" element={<div data-testid="login-route" />} />
          </Routes>
        </MemoryRouter>
      </ToastProvider>
    </ThemeProvider>,
  );
  expect(screen.getByTestId('search')).toHaveTextContent('');
  await fill('Yeni-Parola-123', 'Yeni-Parola-123');
  expect(await screen.findByTestId('login-route')).toBeInTheDocument();
  const call = fakeCalls().find((c) => c.path === '/api/auth/password-reset/confirm/');
  expect(JSON.parse(String(call?.body))).toEqual({ uid: 'MQ', token: 'gizli-token', new_password: 'Yeni-Parola-123' });
});

test('sunucunun parola politikası hatası ilgili alanda gösterilir', async () => {
  renderReset('?uid=MQ&token=t');
  await fill('kisa', 'kisa');
  expect(await screen.findByText(/çok kısa/)).toBeInTheDocument();
});

test('süresi dolmuş bağlantı: backend 400 `token` yanıtı formda anlaşılır hata olarak gösterilir', async () => {
  // Backend (core/auth/serializers.py) süresi dolmuş token için bu gövdeyi döndürür; backend testi:
  // core/tests/test_auth_api.py::test_password_reset_confirm_expired_token_400.
  vi.mocked(fetch).mockResolvedValueOnce(
    new Response(JSON.stringify({ token: ['Bağlantı geçersiz veya süresi dolmuş.'] }), {
      status: 400,
      headers: { 'content-type': 'application/json' },
    }),
  );
  renderReset('?uid=MQ&token=suresi-dolmus');
  await fill('Yeni-Parola-123', 'Yeni-Parola-123');
  expect(await screen.findByRole('alert')).toHaveTextContent('Bağlantı geçersiz veya süresi dolmuş.');
  expect(screen.queryByTestId('login-route')).not.toBeInTheDocument();
  expect(screen.getByRole('link', { name: /Girişe dön/ })).toBeInTheDocument();
});
