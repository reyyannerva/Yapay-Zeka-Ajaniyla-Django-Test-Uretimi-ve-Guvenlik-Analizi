import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, test, vi } from 'vitest';

import { mockProjectStore, resetMockProjects } from '../../lib/api/mock';
import { DeleteConfirm } from './DeleteConfirm';

afterEach(resetMockProjects);

// Örnek veri: 1 numaralı projenin devam eden analizi vardır (409); 3 numaralınınki yoktur.
function renderDelete({ conflict = false, onDeleted = () => undefined } = {}) {
  const project = { id: conflict ? 1 : 3, name: conflict ? 'Örnek Proje A' : 'Örnek Proje C' };
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <DeleteConfirm open project={project} onClose={() => undefined} onDeleted={onDeleted} />
    </QueryClientProvider>,
  );
}

test('aktif analizli proje silinmeye çalışılınca 409 mesajı gösterilir', async () => {
  renderDelete({ conflict: true });
  await userEvent.click(screen.getByRole('button', { name: /Sil/ }));
  expect(await screen.findByText(/devam eden bir analizi/i)).toBeInTheDocument();
  expect(mockProjectStore.projects.some((p) => p.id === 1)).toBe(true);
});

test('silme onay düğmesi tehlike (danger) varyantındadır', () => {
  renderDelete();
  expect(screen.getByRole('button', { name: 'Sil' })).toHaveClass('bg-error');
});

test('başarılı silme projeyi kaldırır ve onDeleted çağrılır', async () => {
  const onDeleted = vi.fn();
  renderDelete({ onDeleted });
  await userEvent.click(screen.getByRole('button', { name: 'Sil' }));
  await vi.waitFor(() => expect(onDeleted).toHaveBeenCalledTimes(1));
  expect(mockProjectStore.projects.some((p) => p.id === 3)).toBe(false);
});

// --- H5-03 / #41: önbellek tutarlılığı ---
function renderWithCache(projectId: number) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const list = { count: 2, next: null, previous: null, results: [{ id: 3, name: 'Örnek Proje C' }, { id: 2, name: 'Örnek Proje B' }] };
  client.setQueryData(['projects', 'list', { page: 1, page_size: 20 }], list);
  client.setQueryData(['analysis-runs', 'list'], []);
  const onDeleted = vi.fn(() => {
    // Yönlendirme anında liste önbelleği zaten güncel olmalı (silinmiş proje bir an bile görünmez).
    snapshot = client.getQueryData(['projects', 'list', { page: 1, page_size: 20 }]);
  });
  let snapshot: unknown;
  render(
    <QueryClientProvider client={client}>
      <DeleteConfirm open project={{ id: projectId, name: 'x' }} onClose={() => undefined} onDeleted={onDeleted} />
    </QueryClientProvider>,
  );
  return { client, onDeleted, getSnapshot: () => snapshot };
}

test('başarılı silmede proje, yönlendirmeden önce önbellekteki listelerden çıkarılır; analiz önbelleği geçersizlenir', async () => {
  const { client, onDeleted, getSnapshot } = renderWithCache(3);
  await userEvent.click(screen.getByRole('button', { name: 'Sil' }));
  await vi.waitFor(() => expect(onDeleted).toHaveBeenCalledTimes(1));
  expect(getSnapshot()).toMatchObject({ count: 1, results: [{ id: 2 }] });
  expect(client.getQueryState(['analysis-runs', 'list'])?.isInvalidated).toBe(true);
});

test('silme başarısızsa (409) kayıt önbellekten kaldırılmaz', async () => {
  const { client, onDeleted } = renderWithCache(1);
  client.setQueryData(['projects', 'list', { page: 1, page_size: 20 }], { count: 1, next: null, previous: null, results: [{ id: 1, name: 'Örnek Proje A' }] });
  await userEvent.click(screen.getByRole('button', { name: 'Sil' }));
  expect(await screen.findByText(/devam eden bir analizi/i)).toBeInTheDocument();
  expect(onDeleted).not.toHaveBeenCalled();
  expect(client.getQueryData(['projects', 'list', { page: 1, page_size: 20 }])).toMatchObject({ results: [{ id: 1 }] });
});
