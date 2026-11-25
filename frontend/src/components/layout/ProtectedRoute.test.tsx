import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';

import type { User } from '../../types';
import { AuthProvider, useAuth } from '../../lib/auth-context';
import { ROUTER_FUTURE } from '../../test/router-future';
import { ProtectedRoute } from './ProtectedRoute';
import { tokenStore } from '../../lib/api/token-store';

// Anonim başlangıç: varsayılan test oturumu temizlenir.
beforeEach(() => tokenStore.clear());

const USER: User = { id: 1, username: 'ornek-kullanici', email: 'ornek@example.test' };

function SessionControls() {
  const { expireSession, isAuthenticated } = useAuth();
  return (
    <div data-testid="dashboard-route">
      <span>{isAuthenticated ? 'oturum-acik' : 'oturum-kapali'}</span>
      <button type="button" onClick={expireSession}>
        Oturumu düşür
      </button>
    </div>
  );
}

function LoginRoute() {
  const { isAuthenticated } = useAuth();
  return (
    <div data-testid="login-route">
      <span>{isAuthenticated ? 'oturum-acik' : 'oturum-kapali'}</span>
    </div>
  );
}

function renderWithRouter(entries: string[], { authenticated }: { authenticated: boolean }) {
  return render(
    <AuthProvider initialUser={authenticated ? USER : null}>
      <MemoryRouter initialEntries={entries} future={ROUTER_FUTURE}>
        <Routes>
          <Route path="/login" element={<LoginRoute />} />
          <Route path="/session-expired" element={<div data-testid="expired-route" />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<SessionControls />} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  );
}

test("kimliksiz kullanıcı /login'e yönlenir", () => {
  renderWithRouter(['/dashboard'], { authenticated: false });
  expect(screen.getByTestId('login-route')).toBeInTheDocument();
  expect(screen.queryByTestId('dashboard-route')).not.toBeInTheDocument();
});

test('kimlikli kullanıcı korunan içeriği görür', () => {
  renderWithRouter(['/dashboard'], { authenticated: true });
  expect(screen.getByTestId('dashboard-route')).toBeInTheDocument();
});

test("expireSession oturumu düşürür ve /session-expired'a yönlendirir", async () => {
  renderWithRouter(['/dashboard'], { authenticated: true });
  await userEvent.click(screen.getByRole('button', { name: 'Oturumu düşür' }));
  expect(screen.getByTestId('expired-route')).toBeInTheDocument();
  expect(screen.queryByTestId('login-route')).not.toBeInTheDocument();
});

test('saklanan oturum doğrulanırken korumalı içerik gösterilmez, doğrulanınca açılır', async () => {
  // Sayfa yenilemesi: yalnızca refresh token var; ProtectedRoute önce sunucu doğrulamasını bekler.
  window.sessionStorage.setItem('testkalkan.refresh', 'test-refresh');
  renderWithRouter(['/dashboard'], { authenticated: false });
  expect(screen.getByRole('status')).toHaveTextContent('Oturum doğrulanıyor');
  expect(screen.queryByTestId('dashboard-route')).not.toBeInTheDocument();
  expect(screen.queryByTestId('login-route')).not.toBeInTheDocument();
  expect(await screen.findByText('oturum-acik')).toBeInTheDocument();
});

test("geçersiz (kara listedeki) saklanmış oturum 'oturum süresi doldu' ekranına düşer ve token temizlenir", async () => {
  window.sessionStorage.setItem('testkalkan.refresh', 'iptal-edilmis');
  vi.mocked(fetch).mockResolvedValueOnce(
    new Response(JSON.stringify({ detail: 'Token is blacklisted', code: 'token_not_valid' }), {
      status: 401,
      headers: { 'content-type': 'application/json' },
    }),
  );
  renderWithRouter(['/dashboard'], { authenticated: false });
  expect(await screen.findByTestId('expired-route')).toBeInTheDocument();
  expect(screen.queryByTestId('dashboard-route')).not.toBeInTheDocument();
  expect(window.sessionStorage.getItem('testkalkan.refresh')).toBeNull();
});
