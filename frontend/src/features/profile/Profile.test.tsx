import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { expect, test, vi } from 'vitest';

import { ToastProvider } from '../../components/ui/Toast';
import { ROUTER_FUTURE } from '../../test/router-future';
import { Profile } from './Profile';

function renderProfile() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ToastProvider>
        <MemoryRouter future={ROUTER_FUTURE}>
          <Profile />
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
}

test('yüklenirken Spinner gösterilir', () => {
  renderProfile();
  expect(screen.getByRole('status')).toBeInTheDocument();
});

test('kullanıcı adı ve e-posta salt-okunur gösterilir', async () => {
  renderProfile();
  const username = await screen.findByLabelText(/Kullanıcı adı/);
  const email = screen.getByLabelText(/E-posta/);
  expect(username).toHaveValue('ornek-kullanici');
  expect(email).toHaveValue('ornek@example.test');
  expect(username).toHaveAttribute('readonly');
  expect(email).toHaveAttribute('readonly');
  expect(screen.getByText(/yönetici/i)).toBeInTheDocument();
});

// H5-03 / #41: backend'de oturum içi parola değiştirme uç noktası yoktur. Önceki örnek form sahte başarı
// gösterdiği için kaldırıldı; kullanıcı gerçek e-posta ile sıfırlama akışına yönlendirilir.
test('parola değişikliği için gerçek sıfırlama akışına yönlendirir; sahte başarı göstermez', async () => {
  renderProfile();
  await screen.findByDisplayValue('ornek@example.test');
  expect(screen.getByRole('link', { name: 'Sıfırlama bağlantısı iste' })).toHaveAttribute('href', '/forgot-password');
  expect(screen.queryByLabelText(/Mevcut parola/)).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /Parolayı değiştir/ })).not.toBeInTheDocument();
});

test('profil bilgisi gerçek /api/auth/me/ uç noktasından okunur', async () => {
  renderProfile();
  await screen.findByDisplayValue('ornek-kullanici');
  expect(vi.mocked(fetch).mock.calls.some(([url]) => String(url).endsWith('/api/auth/me/'))).toBe(true);
});
