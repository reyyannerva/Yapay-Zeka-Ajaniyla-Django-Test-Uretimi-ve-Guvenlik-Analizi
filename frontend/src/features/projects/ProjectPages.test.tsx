import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, expect, test, vi } from 'vitest';

import { ToastProvider } from '../../components/ui/Toast';
import { mockProjectStore, resetMockProjects } from '../../lib/api/mock';
import { getProject } from '../../lib/api/projects';
import { ROUTER_FUTURE } from '../../test/router-future';
import { ProjectDetail } from './ProjectDetail';
import { ProjectEdit } from './ProjectEdit';
import { ProjectNew } from './ProjectNew';

vi.mock('../../lib/api/projects', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../lib/api/projects')>();
  return { ...actual, getProject: vi.fn(actual.getProject) };
});

afterEach(() => {
  resetMockProjects();
  vi.mocked(getProject).mockReset();
});

function renderAt(path: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ToastProvider>
        <MemoryRouter initialEntries={[path]} future={ROUTER_FUTURE}>
          <Routes>
            <Route path="/projects" element={<p>Liste sayfası</p>} />
            <Route path="/projects/new" element={<ProjectNew />} />
            <Route path="/projects/:id" element={<ProjectDetail />} />
            <Route path="/projects/:id/edit" element={<ProjectEdit />} />
          </Routes>
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
}

test('detay: proje bilgisi, arşiv ve doğrulama raporu gösterilir', async () => {
  renderAt('/projects/1');
  expect(await screen.findByRole('heading', { name: 'Örnek Proje A' })).toBeInTheDocument();
  expect(screen.getByText('ornek-a.zip')).toBeInTheDocument();
  expect(screen.getByText('ornek_uygulama')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Düzenle' })).toHaveAttribute('href', '/projects/1/edit');
});

test('detay: olmayan proje için bulunamadı durumu gösterilir', async () => {
  renderAt('/projects/999');
  expect(await screen.findByText('Proje bulunamadı')).toBeInTheDocument();
});

test('detay: silme onayı kırmızı (danger) ve 409 durumunu gösterir', async () => {
  renderAt('/projects/1');
  await userEvent.click(await screen.findByRole('button', { name: 'Projeyi sil' }));
  const confirm = screen.getByRole('button', { name: 'Sil' });
  expect(confirm).toHaveClass('bg-error');
  await userEvent.click(confirm);
  expect(await screen.findByText(/devam eden bir analizi/i)).toBeInTheDocument();
});

test('detay: analizi olmayan proje silinince listeye yönlenir', async () => {
  renderAt('/projects/3');
  await userEvent.click(await screen.findByRole('button', { name: 'Projeyi sil' }));
  await userEvent.click(screen.getByRole('button', { name: 'Sil' }));
  expect(await screen.findByText('Liste sayfası')).toBeInTheDocument();
  expect(mockProjectStore.projects.some((p) => p.id === 3)).toBe(false);
});

test('detay: silme sonrası silinen projenin detayı yeniden çekilmez, "Proje bulunamadı" görünmez', async () => {
  const actual = await vi.importActual<typeof import('../../lib/api/projects')>('../../lib/api/projects');
  vi.mocked(getProject).mockImplementation(actual.getProject);
  renderAt('/projects/3');
  await userEvent.click(await screen.findByRole('button', { name: 'Projeyi sil' }));
  // Gerçek ağ gecikmesini taklit et: silme sonrası yapılacak herhangi bir yeniden çekim geç ve 404 döner.
  vi.mocked(getProject).mockClear();
  vi.mocked(getProject).mockImplementation(async (id) => {
    await new Promise((resolve) => setTimeout(resolve, 30));
    return actual.getProject(id);
  });
  let flashed = false;
  const observer = new MutationObserver(() => {
    const text = document.body.textContent ?? '';
    if (text.includes('Proje bulunamadı') || text.includes('Yükleniyor')) flashed = true;
  });
  observer.observe(document.body, { childList: true, subtree: true, characterData: true });
  await userEvent.click(screen.getByRole('button', { name: 'Sil' }));
  expect(await screen.findByText('Liste sayfası')).toBeInTheDocument();
  await new Promise((resolve) => setTimeout(resolve, 100));
  observer.disconnect();
  expect(flashed).toBe(false);
  expect(getProject).not.toHaveBeenCalled();
  expect(screen.queryByText('Proje bulunamadı')).not.toBeInTheDocument();
});

test('düzenleme: ad güncellenir ve detaya dönülür; boş ad reddedilir', async () => {
  renderAt('/projects/3/edit');
  const name = await screen.findByLabelText('Proje adı');
  expect(name).toHaveValue('Örnek Proje C');
  await userEvent.clear(name);
  await userEvent.click(screen.getByRole('button', { name: 'Kaydet' }));
  expect(await screen.findByText('Proje adı zorunludur.')).toBeInTheDocument();
  await userEvent.type(name, 'Yeniden Adlandı');
  await userEvent.click(screen.getByRole('button', { name: 'Kaydet' }));
  expect(await screen.findByRole('heading', { name: 'Yeniden Adlandı' })).toBeInTheDocument();
});

test('düzenleme: başka projenin adı sunucu mesajıyla reddedilir', async () => {
  renderAt('/projects/3/edit');
  const name = await screen.findByLabelText('Proje adı');
  await userEvent.clear(name);
  await userEvent.type(name, 'Örnek Proje A');
  await userEvent.click(screen.getByRole('button', { name: 'Kaydet' }));
  expect(await screen.findByText('Bu adla kayıtlı bir projeniz zaten var.')).toBeInTheDocument();
});

test('yeni proje sayfası ProjectUpload formunu gösterir ve başarıda detaya yönlendirir', async () => {
  renderAt('/projects/new');
  const file = new File(['x'], 'yeni.zip', { type: 'application/zip' });
  await userEvent.upload(await screen.findByLabelText('Proje arşivi'), file);
  await userEvent.type(screen.getByLabelText('Proje adı'), 'Sayfadan Yüklenen');
  await userEvent.click(screen.getByRole('button', { name: 'Projeyi yükle' }));
  await vi.waitFor(() =>
    expect(screen.getByRole('heading', { name: 'Sayfadan Yüklenen' })).toBeInTheDocument(),
  );
});
