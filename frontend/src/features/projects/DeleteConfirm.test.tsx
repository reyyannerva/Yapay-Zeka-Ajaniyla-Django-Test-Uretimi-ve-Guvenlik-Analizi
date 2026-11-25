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
