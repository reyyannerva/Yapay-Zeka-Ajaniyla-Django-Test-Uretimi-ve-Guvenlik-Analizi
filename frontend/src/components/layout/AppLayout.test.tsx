import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { expect, test } from 'vitest';

import type { User } from '../../types';
import { AuthProvider } from '../../lib/auth-context';
import { ThemeProvider } from '../../lib/theme-context';
import { AppLayout } from './AppLayout';
import { ProtectedRoute } from './ProtectedRoute';

const USER: User = { id: 1, username: 'ornek-kullanici', email: 'ornek@example.test' };

function renderLayout() {
  return render(
    <ThemeProvider>
      <AuthProvider initialUser={USER}>
        <MemoryRouter initialEntries={['/projects']}>
          <Routes>
            <Route path="/login" element={<div data-testid="login-route" />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/projects" element={<div data-testid="projects-route" />} />
              </Route>
            </Route>
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </ThemeProvider>,
  );
}

test('kenar menüsü ana linkleri ve tema düğmesini içerir', () => {
  renderLayout();
  expect(screen.getByRole('link', { name: /Genel bakış/ })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /Projeler/ })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /tema/i })).toBeInTheDocument();
  expect(screen.getByTestId('projects-route')).toBeInTheDocument();
});

test('Analizler ve Raporlar pasif yer tutucudur (link değil)', () => {
  renderLayout();
  expect(screen.queryByRole('link', { name: /Analizler/ })).not.toBeInTheDocument();
  expect(screen.queryByRole('link', { name: /Raporlar/ })).not.toBeInTheDocument();
  expect(screen.getByText('Analizler').closest('[aria-disabled="true"]')).not.toBeNull();
  expect(screen.getByText('Raporlar').closest('[aria-disabled="true"]')).not.toBeNull();
});

test('kullanıcı menüsünden çıkış yapınca /login açılır', async () => {
  renderLayout();
  await userEvent.click(screen.getByRole('button', { name: /Kullanıcı menüsü/ }));
  await userEvent.click(screen.getByRole('menuitem', { name: /Çıkış yap/ }));
  expect(screen.getByTestId('login-route')).toBeInTheDocument();
});
