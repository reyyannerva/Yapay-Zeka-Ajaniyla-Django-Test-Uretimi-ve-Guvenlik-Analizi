import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, test, vi } from 'vitest';

import { resetMockProjects } from '../../lib/api/mock';
import type { Project } from '../../types';
import { fakeCalls } from '../../test/fake-api';
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

// --- H5-03 / #41: gerçek multipart sözleşmesi ---
test('yükleme multipart/form-data ile (name, description, archive) gönderilir; Content-Type elle yazılmaz', async () => {
  renderUpload();
  await selectFile(fileOfSize('proje.zip', MIB));
  await userEvent.type(screen.getByLabelText('Proje adı'), 'Multipart Proje');
  await userEvent.type(screen.getByLabelText('Açıklama (isteğe bağlı)'), 'Açıklama');
  await userEvent.click(screen.getByRole('button', { name: 'Projeyi yükle' }));
  await vi.waitFor(() => expect(fakeCalls().some((c) => c.method === 'POST' && c.path === '/api/projects/')).toBe(true));
  const call = fakeCalls().find((c) => c.method === 'POST' && c.path === '/api/projects/')!;
  expect(call.body).toBeInstanceOf(FormData);
  const form = call.body as FormData;
  expect(form.get('name')).toBe('Multipart Proje');
  expect(form.get('description')).toBe('Açıklama');
  expect((form.get('archive') as File).name).toBe('proje.zip');
  expect(call.headers.has('Content-Type')).toBe(false);
});

test('yükleme sürerken düğme pasifleşir ve çift gönderim yapılmaz', async () => {
  let release!: (r: Response) => void;
  vi.mocked(fetch).mockImplementationOnce(() => new Promise<Response>((r) => (release = r)));
  renderUpload();
  await selectFile(fileOfSize('proje.zip', MIB));
  await userEvent.type(screen.getByLabelText('Proje adı'), 'Tek Gönderim');
  await userEvent.click(screen.getByRole('button', { name: 'Projeyi yükle' }));
  const busy = await screen.findByRole('button', { name: 'Yükleniyor…' });
  expect(busy).toBeDisabled();
  expect(screen.getByText(/güvenlik denetiminden geçiriliyor/)).toBeInTheDocument();
  await userEvent.click(busy);
  expect(vi.mocked(fetch).mock.calls.filter(([u]) => String(u).endsWith('/api/projects/'))).toHaveLength(1);
  release(new Response(JSON.stringify({ detail: 'x' }), { status: 500, headers: { 'content-type': 'application/json' } }));
  expect(await screen.findByRole('alert')).toHaveTextContent(/tamamlanamadı|beklenmeyen/i);
});

test('sunucunun arşiv reddi (bozuk ZIP) arşiv alanında anlaşılır mesajla gösterilir', async () => {
  vi.mocked(fetch).mockResolvedValueOnce(
    new Response(JSON.stringify({ archive: [{ code: 'CORRUPT_ARCHIVE', detail: 'Arşiv bozuk.' }] }), {
      status: 400,
      headers: { 'content-type': 'application/json' },
    }),
  );
  renderUpload();
  await selectFile(fileOfSize('bozuk.zip', MIB));
  await userEvent.type(screen.getByLabelText('Proje adı'), 'Bozuk');
  await userEvent.click(screen.getByRole('button', { name: 'Projeyi yükle' }));
  expect(await screen.findByText('Arşiv bozuk görünüyor; dosyayı yeniden oluşturup deneyin.')).toBeInTheDocument();
});

test('bağlantı kesilirse yükleme başarısız sayılır ve kullanıcı bilgilendirilir', async () => {
  vi.mocked(fetch).mockRejectedValueOnce(new TypeError('Failed to fetch'));
  const onUploaded = vi.fn();
  renderUpload(onUploaded);
  await selectFile(fileOfSize('proje.zip', MIB));
  await userEvent.type(screen.getByLabelText('Proje adı'), 'Kopan');
  await userEvent.click(screen.getByRole('button', { name: 'Projeyi yükle' }));
  expect(await screen.findByRole('alert')).toBeInTheDocument();
  expect(onUploaded).not.toHaveBeenCalled();
});
