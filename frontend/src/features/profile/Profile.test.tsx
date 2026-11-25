import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { expect, test } from 'vitest';

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

async function fill(current: string, next: string, confirm: string) {
  await screen.findByDisplayValue('ornek@example.test');
  if (current) await userEvent.type(screen.getByLabelText(/Mevcut parola/), current);
  if (next) await userEvent.type(screen.getByLabelText(/^Yeni parola$/), next);
  if (confirm) await userEvent.type(screen.getByLabelText(/Yeni parola \(tekrar\)/), confirm);
  await userEvent.click(screen.getByRole('button', { name: /Parolayı değiştir/ }));
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

test('boş yeni parola hata verir', async () => {
  renderProfile();
  await fill('mevcut-parola', '', '');
  expect(await screen.findByText(/Yeni parola zorunludur/)).toBeInTheDocument();
  expect(screen.queryByText(/Parolanız güncellendi/)).not.toBeInTheDocument();
});

test('zayıf (kısa) yeni parola hata verir', async () => {
  renderProfile();
  await fill('mevcut-parola', 'kisa', 'kisa');
  expect(await screen.findByText(/en az 8 karakter/i)).toBeInTheDocument();
  expect(screen.queryByText(/Parolanız güncellendi/)).not.toBeInTheDocument();
});

test('yalnızca rakamlardan oluşan yeni parola hata verir', async () => {
  renderProfile();
  await fill('mevcut-parola', '123456789', '123456789');
  expect(await screen.findByText(/yalnızca rakam/i)).toBeInTheDocument();
});

test('mevcut parola boşsa ve tekrar eşleşmiyorsa hata verir', async () => {
  renderProfile();
  await fill('', 'yeni-parola-ornek', 'baska-parola-ornek');
  expect(await screen.findByText(/Mevcut parola zorunludur/)).toBeInTheDocument();
  expect(screen.getByText(/eşleşmiyor/i)).toBeInTheDocument();
});

test('yeni parola mevcut parolayla aynı olamaz', async () => {
  renderProfile();
  await fill('ayni-parola-ornek', 'ayni-parola-ornek', 'ayni-parola-ornek');
  expect(await screen.findByText(/farklı olmalı/i)).toBeInTheDocument();
});

test('geçerli giriş toast ile onaylanır ve form temizlenir', async () => {
  renderProfile();
  await fill('mevcut-parola', 'yeni-parola-ornek', 'yeni-parola-ornek');
  expect(await screen.findByText(/Parolanız güncellendi/)).toBeInTheDocument();
  expect(screen.getByLabelText(/Mevcut parola/)).toHaveValue('');
  expect(screen.getByLabelText(/^Yeni parola$/)).toHaveValue('');
});
