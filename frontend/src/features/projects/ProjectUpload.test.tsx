import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, test, vi } from 'vitest';

import { resetMockProjects } from '../../lib/api/mock';
import type { Project } from '../../types';
import { ProjectUpload } from './ProjectUpload';

afterEach(resetMockProjects);

const MIB = 1024 * 1024;

function renderUpload(onUploaded: (project: Project) => void = () => undefined) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ProjectUpload onUploaded={onUploaded} />
    </QueryClientProvider>,
  );
}

// Tarayıcı `accept` ile süzer; testte süzme kapatılır ki istemci doğrulaması sınansın.
async function selectFile(file: File) {
  const user = userEvent.setup({ applyAccept: false });
  await user.upload(screen.getByLabelText('Proje arşivi'), file);
}

function fileOfSize(name: string, bytes: number): File {
  const file = new File(['x'], name, { type: 'application/zip' });
  Object.defineProperty(file, 'size', { value: bytes });
  return file;
}

test('50 MiB üstü arşiv seçilince boyut hatası gösterilir, form çökmez', async () => {
  renderUpload();
  await selectFile(fileOfSize('buyuk.zip', 50 * MIB + 1));
  expect(await screen.findByText(/en fazla 50 ?MiB|boyut/i)).toBeInTheDocument();
  // Form hâlâ kullanılabilir.
  expect(screen.getByLabelText('Proje adı')).toBeEnabled();
  expect(screen.getByRole('button', { name: 'Projeyi yükle' })).toBeEnabled();
});

test('tam 50 MiB olan arşiv kabul edilir', async () => {
  renderUpload();
  await selectFile(fileOfSize('sinir.zip', 50 * MIB));
  await userEvent.type(screen.getByLabelText('Proje adı'), 'Sınır');
  await userEvent.click(screen.getByRole('button', { name: 'Projeyi yükle' }));
  expect(screen.queryByText(/en fazla 50 ?MiB/i)).not.toBeInTheDocument();
});

test('.zip olmayan dosya reddedilir', async () => {
  renderUpload();
  await selectFile(new File([], 'x.tar'));
  expect(await screen.findByText(/\.zip/i)).toBeInTheDocument();
});

test('ad ve arşiv boşken gönderilemez; alan hataları gösterilir', async () => {
  const onUploaded = vi.fn();
  renderUpload(onUploaded);
  await userEvent.click(screen.getByRole('button', { name: 'Projeyi yükle' }));
  expect(await screen.findByText('Proje adı zorunludur.')).toBeInTheDocument();
  expect(screen.getByText('Bir .zip arşivi seçin.')).toBeInTheDocument();
  expect(onUploaded).not.toHaveBeenCalled();
});

test('geçerli yükleme onUploaded ile oluşan projeyi verir', async () => {
  const onUploaded = vi.fn();
  renderUpload(onUploaded);
  await selectFile(fileOfSize('yeni.zip', 2 * MIB));
  await userEvent.type(screen.getByLabelText('Proje adı'), 'Yeni Proje');
  await userEvent.click(screen.getByRole('button', { name: 'Projeyi yükle' }));
  await vi.waitFor(() => expect(onUploaded).toHaveBeenCalledTimes(1));
  expect(onUploaded.mock.calls[0][0]).toMatchObject({ name: 'Yeni Proje', id: 4 });
});

test('aynı adlı proje için sunucu hatası ad alanında anlaşılır mesajla gösterilir', async () => {
  renderUpload();
  await selectFile(fileOfSize('yeni.zip', MIB));
  await userEvent.type(screen.getByLabelText('Proje adı'), 'Örnek Proje A');
  await userEvent.click(screen.getByRole('button', { name: 'Projeyi yükle' }));
  expect(await screen.findByText('Bu adla kayıtlı bir projeniz zaten var.')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Projeyi yükle' })).toBeEnabled();
});
