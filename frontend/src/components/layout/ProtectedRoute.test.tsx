import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { expect, test } from 'vitest';

import type { User } from '../../types';
import { AuthProvider, useAuth } from '../../lib/auth-context';
import { ROUTER_FUTURE } from '../../test/router-future';
import { ProtectedRoute } from './ProtectedRoute';

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

function SignInControls() {
  const { signInMock, isAuthenticated } = useAuth();
  return (
    <div data-testid="login-route">
      <span>{isAuthenticated ? 'oturum-acik' : 'oturum-kapali'}</span>
      <button type="button" onClick={() => signInMock(USER)}>
        Mock giriş
      </button>
    </div>
  );
}

function renderWithRouter(entries: string[], { authenticated }: { authenticated: boolean }) {
  return render(
    <AuthProvider initialUser={authenticated ? USER : null}>
      <MemoryRouter initialEntries={entries} future={ROUTER_FUTURE}>
        <Routes>
          <Route path="/login" element={<SignInControls />} />
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

test('signInMock kullanıcıyı atar ve isAuthenticated true olur', async () => {
  renderWithRouter(['/login'], { authenticated: false });
  expect(screen.getByText('oturum-kapali')).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: 'Mock giriş' }));
  expect(screen.getByText('oturum-acik')).toBeInTheDocument();
});
