import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, expect, test } from 'vitest';

import { mockProjectStore, resetMockProjects } from '../../lib/api/mock';
import { ROUTER_FUTURE } from '../../test/router-future';
import type { Project } from '../../types';
import { ProjectList } from './ProjectList';

afterEach(resetMockProjects);

function renderList({ projects }: { projects?: Project[] } = {}) {
  if (projects) mockProjectStore.projects = projects;
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter future={ROUTER_FUTURE}>
        <ProjectList />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

test('hiç proje yokken boş durum (14) gösterilir', async () => {
  renderList({ projects: [] });
  expect(await screen.findByText(/ilk projenizi|henüz proje yok/i)).toBeInTheDocument();
  expect(screen.getAllByRole('link', { name: /yeni proje/i })[0]).toHaveAttribute(
    'href',
    '/projects/new',
  );
});

test('projeler tabloda listelenir; ad detay bağlantısıdır ve doğrulama durumu etiketlidir', async () => {
  renderList();
  const table = await screen.findByRole('table');
  expect(within(table).getAllByRole('row')).toHaveLength(4); // 3 proje + başlık
  expect(within(table).getByRole('link', { name: 'Örnek Proje A' })).toHaveAttribute(
    'href',
    '/projects/1',
  );
  expect(within(table).getByText('Doğrulandı')).toHaveAttribute('data-tone', 'pass');
  expect(within(table).getByText('Geçersiz')).toHaveAttribute('data-tone', 'error');
  expect(within(table).getByText('Bekliyor')).toBeInTheDocument();
});

test('yüklenirken Spinner gösterilir', () => {
  renderList();
  expect(screen.getByRole('status')).toBeInTheDocument();
});
