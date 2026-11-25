import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, expect, test } from 'vitest';

import { resetMockProjects } from '../../lib/api/mock';
import { ROUTER_FUTURE } from '../../test/router-future';
import { Overview } from './Overview';

afterEach(resetMockProjects);

function renderOverview() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter future={ROUTER_FUTURE}>
        <Overview />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

test('yüklenirken Spinner gösterilir', () => {
  renderOverview();
  expect(screen.getByRole('status')).toBeInTheDocument();
});

test('yüklenince metrik kartları ve son analizler tablosu görünür', async () => {
  renderOverview();
  expect(await screen.findByText('Toplam proje')).toBeInTheDocument();
  expect(screen.getByText('Devam eden analiz')).toBeInTheDocument();
  const table = screen.getByRole('table');
  // 6 örnek analiz (#40 ile 3 DEMO analiz eklendi) + başlık satırı
  expect(within(table).getAllByRole('row')).toHaveLength(7);
  expect(within(table).getByRole('link', { name: '#3' })).toHaveAttribute('href', '/analyses/3');
});

test('metrikler açıkça örnek veri olarak etiketlenir', async () => {
  renderOverview();
  await screen.findByText('Toplam proje');
  expect(screen.getAllByText(/örnek/i).length).toBeGreaterThan(0);
});

test('devam eden analiz için aşama şeridi görünür ve son düğüm "Tamamlandı"dır', async () => {
  renderOverview();
  const strip = await screen.findByRole('list', { name: 'Analiz aşamaları' });
  const items = within(strip).getAllByRole('listitem');
  expect(items[items.length - 1]).toHaveTextContent('Tamamlandı');
  expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '40');
});

test('LLM yalnızca sağlayıcı olarak gösterilir, model kimliği yazılmaz', async () => {
  renderOverview();
  const table = await screen.findByRole('table');
  expect(within(table).getAllByText('Groq').length).toBeGreaterThan(0);
  expect(screen.queryByText(/ornek-model/)).not.toBeInTheDocument();
});

test('doğrulanmış bulgu FindingBadge ile gösterilir ve başarı tonu almaz', async () => {
  renderOverview();
  const table = await screen.findByRole('table');
  const badge = within(table).getByText('Doğrulanmış');
  expect(badge).toHaveAttribute('data-tone', 'error');
  expect(badge).not.toHaveAttribute('data-tone', 'pass');
});
