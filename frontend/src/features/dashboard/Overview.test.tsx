import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, expect, test, vi } from 'vitest';

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
  // Sahte API'deki 6 analiz kaydı + başlık satırı
  expect(within(table).getAllByRole('row')).toHaveLength(7);
  expect(within(table).getByRole('link', { name: '#3' })).toHaveAttribute('href', '/analyses/3');
});

// H5-03 / #41: metrikler artık API yanıtından hesaplanır; "Örnek veri" etiketi gerçek veriyi yanlış tanıtırdı.
test('metrikler API verisinden hesaplanır ve örnek veri olarak etiketlenmez', async () => {
  renderOverview();
  const metrics = await screen.findByRole('region', { name: 'Metrikler' });
  expect(within(metrics).getByText('Toplam proje').nextElementSibling).toHaveTextContent('3');
  expect(within(metrics).queryByText('Örnek veri')).not.toBeInTheDocument();
  expect(vi.mocked(fetch).mock.calls.some(([url]) => String(url).includes('/api/projects/'))).toBe(true);
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

// H5-03 / #41: gerçek analiz kimliklerine örnek güvenlik bulgusu eşlenmez (sahte sonuç üretilmez).
test('gerçek analiz satırlarına örnek güvenlik bulgusu eklenmez', async () => {
  renderOverview();
  const table = await screen.findByRole('table');
  expect(within(table).queryByText('Doğrulanmış')).not.toBeInTheDocument();
  expect(within(table).queryByText(/Güvenlik bulgusu/)).not.toBeInTheDocument();
  expect(screen.getByText('Tamamlanan analiz')).toBeInTheDocument();
});
