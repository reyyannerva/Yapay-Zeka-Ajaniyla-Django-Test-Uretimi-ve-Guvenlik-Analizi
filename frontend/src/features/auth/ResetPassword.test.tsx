import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { expect, test } from 'vitest';

import { ToastProvider } from '../../components/ui/Toast';
import { ThemeProvider } from '../../lib/theme-context';
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
