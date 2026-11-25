import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { expect, test } from 'vitest';

import type { User } from '../../types';
import { AuthProvider } from '../../lib/auth-context';
import { ROUTER_FUTURE } from '../../test/router-future';
import { ForgotPassword } from './ForgotPassword';
import { SessionExpired } from './SessionExpired';

const USER: User = { id: 1, username: 'ornek-kullanici', email: 'ornek@example.test' };

test('şifre sıfırlama talebi hesabın varlığını ifşa etmeyen genel onay gösterir', async () => {
  render(
    <MemoryRouter future={ROUTER_FUTURE}>
      <ForgotPassword />
    </MemoryRouter>,
  );
  await userEvent.type(screen.getByLabelText(/E-posta/), 'kayitsiz@example.test');
  await userEvent.click(screen.getByRole('button', { name: /Bağlantı gönder/ }));
  expect(await screen.findByRole('status')).toHaveTextContent(/kayıtlıysa/i);
});

test('geçersiz e-posta biçimi alan hatası gösterir', async () => {
  render(
    <MemoryRouter future={ROUTER_FUTURE}>
      <ForgotPassword />
    </MemoryRouter>,
  );
  await userEvent.type(screen.getByLabelText(/E-posta/), 'gecersiz');
  await userEvent.click(screen.getByRole('button', { name: /Bağlantı gönder/ }));
  expect(await screen.findByText(/geçerli bir e-posta/i)).toBeInTheDocument();
});

test("SessionExpired oturumu temizler ve /login'e yönlendirir", async () => {
  render(
    <AuthProvider initialUser={USER}>
      <MemoryRouter initialEntries={['/session-expired']} future={ROUTER_FUTURE}>
        <Routes>
          <Route path="/session-expired" element={<SessionExpired />} />
          <Route path="/login" element={<div data-testid="login-route" />} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  );
  await userEvent.click(screen.getByRole('button', { name: /Yeniden giriş yap/ }));
  expect(screen.getByTestId('login-route')).toBeInTheDocument();
});
