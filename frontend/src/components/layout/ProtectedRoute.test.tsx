import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { expect, test } from 'vitest';

import type { User } from '../../types';
import { AuthProvider } from '../../lib/auth-context';
import { ProtectedRoute } from './ProtectedRoute';

const USER: User = { id: 1, username: 'ornek-kullanici', email: 'ornek@example.test' };

function renderWithRouter(entries: string[], { authenticated }: { authenticated: boolean }) {
  return render(
    <AuthProvider initialUser={authenticated ? USER : null}>
      <MemoryRouter initialEntries={entries}>
        <Routes>
          <Route path="/login" element={<div data-testid="login-route" />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<div data-testid="dashboard-route" />} />
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
