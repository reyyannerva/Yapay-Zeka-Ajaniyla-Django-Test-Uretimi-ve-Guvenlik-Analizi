import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, expect, test } from 'vitest';

import { ToastProvider } from '../../components/ui/Toast';
import { resetMockLoginAttempts } from '../../lib/api/auth';
import { AuthProvider } from '../../lib/auth-context';
import { ROUTER_FUTURE } from '../../test/router-future';
import { Login } from './Login';

// Mock servis: "yanlis-parola" yanlış sayılır (1-2. deneme 401, 3. deneme 429 kilit). Değerler örnektir.
const WRONG = { email: 'ornek@example.test', password: 'yanlis-parola' };
const RIGHT = { email: 'ornek@example.test', password: 'dogru-parola-ornek' };

beforeEach(() => {
  resetMockLoginAttempts();
});

function renderLogin() {
  return render(
    <ToastProvider>
      <AuthProvider>
        <MemoryRouter initialEntries={['/login']} future={ROUTER_FUTURE}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={<div data-testid="dashboard-route" />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </ToastProvider>,
  );
}

async function submit(creds: { email: string; password: string }) {
  await userEvent.clear(screen.getByLabelText(/E-posta/));
  await userEvent.clear(screen.getByLabelText(/Parola/));
  await userEvent.type(screen.getByLabelText(/E-posta/), creds.email);
  await userEvent.type(screen.getByLabelText(/Parola/), creds.password);
  await userEvent.click(screen.getByRole('button', { name: /Giriş/ }));
}

test('boş form zorunlu alan hatası gösterir', async () => {
  renderLogin();
  await userEvent.click(screen.getByRole('button', { name: /Giriş/ }));
  expect(await screen.findByText(/zorunlu/i)).toBeInTheDocument();
});

test('3. hatalı denemede kilit uyarısı ve 15 dk bilgisi gösterilir, kalan süre uydurulmaz', async () => {
  renderLogin();
  await submit(WRONG);
  await submit(WRONG);
  // 1. ve 2. denemede kilit yok, yalnızca genel kimlik hatası
  expect(screen.queryByText(/geçici olarak kilitlendi/i)).not.toBeInTheDocument();
  await submit(WRONG);
  expect(await screen.findByText(/geçici olarak kilitlendi|15 dk/i)).toBeInTheDocument();
  expect(screen.queryByText(/kalan süre: \d/i)).not.toBeInTheDocument();
});

test('1. hatalı denemede kimlik hatası gösterilir, kilit uyarısı gösterilmez', async () => {
  renderLogin();
  await submit(WRONG);
  expect(await screen.findByRole('alert')).toHaveTextContent(/hatalı/i);
  expect(screen.queryByText(/kilitlendi/i)).not.toBeInTheDocument();
});

test('form "E-posta" etiketi gösterir (değer username\'e eşlenir)', () => {
  renderLogin();
  expect(screen.getByLabelText(/E-posta/)).toBeInTheDocument();
});

test("başarılı girişte /dashboard'a yönlenir", async () => {
  renderLogin();
  await submit(RIGHT);
  expect(await screen.findByTestId('dashboard-route')).toBeInTheDocument();
});
