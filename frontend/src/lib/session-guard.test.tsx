import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { expect, test } from 'vitest';

import { ProtectedRoute } from '../components/layout/ProtectedRoute';
import { SessionExpired } from '../features/auth/SessionExpired';
import type { ApiError, User } from '../types';
import { ROUTER_FUTURE } from '../test/router-future';
import { AuthProvider } from './auth-context';
import { ThemeProvider } from './theme-context';
import { SessionGuard } from './session-guard';

const USER: User = { id: 1, username: 'ornek-kullanici', email: 'ornek@example.test' };

function Protected({ status }: { status: ApiError['status'] }) {
  const query = useQuery({
    queryKey: ['guard-test', status],
    queryFn: () => Promise.reject<never>({ status, body: { detail: 'hata' } } satisfies ApiError),
    retry: false,
  });
  return <p>{query.isError ? 'sorgu-hatasi' : 'yukleniyor'}</p>;
}

function renderApp(status: ApiError['status']) {
  const client = new QueryClient();
  return render(
    <ThemeProvider>
    <QueryClientProvider client={client}>
      <AuthProvider initialUser={USER}>
        <MemoryRouter initialEntries={['/dashboard']} future={ROUTER_FUTURE}>
          <SessionGuard />
          <Routes>
            <Route path="/login" element={<p>Giriş sayfası</p>} />
            <Route path="/session-expired" element={<SessionExpired />} />
            <Route element={<ProtectedRoute />}>
              <Route path="/dashboard" element={<Protected status={status} />} />
            </Route>
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>
    </ThemeProvider>,
  );
}

test('sorgu 401 dönünce oturum düşer ve oturum süresi doldu ekranı (12) açılır', async () => {
  renderApp(401);
  expect(await screen.findByRole('heading', { name: 'Oturum süreniz doldu' })).toBeInTheDocument();
});

test('401 dışındaki hatalar (403) oturumu düşürmez', async () => {
  renderApp(403);
  expect(await screen.findByText('sorgu-hatasi')).toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: 'Oturum süreniz doldu' })).not.toBeInTheDocument();
});
