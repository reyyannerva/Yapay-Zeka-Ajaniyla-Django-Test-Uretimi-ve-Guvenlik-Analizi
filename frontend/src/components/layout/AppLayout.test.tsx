import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { expect, test } from 'vitest';

import type { User } from '../../types';
import { AuthProvider } from '../../lib/auth-context';
import { ThemeProvider } from '../../lib/theme-context';
import { ROUTER_FUTURE } from '../../test/router-future';
import { AppLayout } from './AppLayout';
import { ProtectedRoute } from './ProtectedRoute';

const USER: User = { id: 1, username: 'ornek-kullanici', email: 'ornek@example.test' };

function renderLayout() {
  return render(
    <ThemeProvider>
      <AuthProvider initialUser={USER}>
        <MemoryRouter initialEntries={['/projects']} future={ROUTER_FUTURE}>
          <Routes>
            <Route path="/login" element={<div data-testid="login-route" />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/projects" element={<div data-testid="projects-route" />} />
                <Route path="/dashboard" element={<div data-testid="dashboard-route" />} />
                <Route path="/profile" element={<div data-testid="profile-route" />} />
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

test('geçerli sayfanın linki aktif (aria-current) işaretlenir', () => {
  renderLayout();
  expect(screen.getByRole('link', { name: /Projeler/ })).toHaveAttribute('aria-current', 'page');
  expect(screen.getByRole('link', { name: /Genel bakış/ })).not.toHaveAttribute('aria-current');
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

test('kullanıcı menüsündeki Profil linki /profile açar', async () => {
  renderLayout();
  await userEvent.click(screen.getByRole('button', { name: /Kullanıcı menüsü/ }));
  const link = screen.getByRole('menuitem', { name: 'Profil' });
  expect(link).toHaveAttribute('href', '/profile');
  await userEvent.click(link);
  expect(screen.getByTestId('profile-route')).toBeInTheDocument();
  expect(screen.queryByRole('menu')).not.toBeInTheDocument();
});

test('mobil: hamburger menüyü açar; Escape, örtü ve link seçimi kapatır', async () => {
  renderLayout();
  const toggle = screen.getByRole('button', { name: 'Menüyü aç' });
  expect(toggle).toHaveAttribute('aria-expanded', 'false');
  expect(screen.queryByTestId('sidebar-scrim')).not.toBeInTheDocument();

  await userEvent.click(toggle);
  expect(toggle).toHaveAttribute('aria-expanded', 'true');
  expect(screen.getByTestId('sidebar-scrim')).toBeInTheDocument();

  await userEvent.keyboard('{Escape}');
  expect(toggle).toHaveAttribute('aria-expanded', 'false');
  expect(screen.queryByTestId('sidebar-scrim')).not.toBeInTheDocument();

  await userEvent.click(toggle);
  await userEvent.click(screen.getByTestId('sidebar-scrim'));
  expect(toggle).toHaveAttribute('aria-expanded', 'false');

  await userEvent.click(toggle);
  await userEvent.click(screen.getByRole('link', { name: /Genel bakış/ }));
  expect(screen.getByTestId('dashboard-route')).toBeInTheDocument();
  expect(toggle).toHaveAttribute('aria-expanded', 'false');
});
