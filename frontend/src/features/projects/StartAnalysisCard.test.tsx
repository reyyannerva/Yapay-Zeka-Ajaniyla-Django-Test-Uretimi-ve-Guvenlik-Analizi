import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, useParams } from 'react-router-dom';
import { expect, test, vi } from 'vitest';

import { ToastProvider } from '../../components/ui/Toast';
import { mockProjectStore } from '../../lib/api/mock';
import { fakeCalls } from '../../test/fake-api';
import { ROUTER_FUTURE } from '../../test/router-future';
import { StartAnalysisCard } from './StartAnalysisCard';

function RunRoute() {
  return <div data-testid="run-route">{useParams().id}</div>;
}

function renderCard(projectId = 3) {
  const project = mockProjectStore.projects.find((p) => p.id === projectId)!;
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ToastProvider>
        <MemoryRouter initialEntries={['/projects/3']} future={ROUTER_FUTURE}>
          <Routes>
            <Route path="/projects/:id" element={<StartAnalysisCard project={project} />} />
            <Route path="/analyses/:id" element={<RunRoute />} />
          </Routes>
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
}

const posts = () => fakeCalls().filter((c) => c.method === 'POST' && c.path === '/api/analysis-runs/');

test('kural tabanlı analiz: LLM alanları gönderilmez, kayıt oluşunca detayına gidilir', async () => {
  renderCard();
  expect(screen.getByLabelText('Model')).toBeDisabled();
  await userEvent.click(screen.getByRole('button', { name: 'Analiz başlat' }));
  expect(await screen.findByTestId('run-route')).toHaveTextContent('100');
  expect(JSON.parse(String(posts()[0]!.body))).toEqual({ project: 3, method: 'RULE_BASED', fallback_enabled: true });
});

test('LLM yönteminde model zorunludur; boşsa istek gönderilmez', async () => {
  renderCard();
  await userEvent.selectOptions(screen.getByLabelText('Yöntem'), 'HYBRID');
  await userEvent.click(screen.getByRole('button', { name: 'Analiz başlat' }));
  expect(await screen.findByText('LLM yöntemlerinde model adı zorunludur.')).toBeInTheDocument();
  expect(posts()).toHaveLength(0);
});

test('LLM yöntemi sağlayıcı/model ile gönderilir', async () => {
  renderCard();
  await userEvent.selectOptions(screen.getByLabelText('Yöntem'), 'DIRECT_LLM');
  await userEvent.selectOptions(screen.getByLabelText('LLM sağlayıcı'), 'OLLAMA');
  await userEvent.type(screen.getByLabelText('Model'), 'llama3');
  await userEvent.click(screen.getByLabelText(/fallback/));
  await userEvent.click(screen.getByRole('button', { name: 'Analiz başlat' }));
  await screen.findByTestId('run-route');
  expect(JSON.parse(String(posts()[0]!.body))).toEqual({
    project: 3,
    method: 'DIRECT_LLM',
    llm_provider: 'OLLAMA',
    llm_model: 'llama3',
    fallback_enabled: false,
  });
});

test('sunucu reddi (ör. aktif analiz var) kullanıcıya gösterilir, yönlendirme yapılmaz', async () => {
  vi.mocked(fetch).mockResolvedValueOnce(
    new Response(JSON.stringify({ project: ['Bu proje için zaten aktif (sonlanmamış) bir analiz var.'] }), {
      status: 400,
      headers: { 'content-type': 'application/json' },
    }),
  );
  renderCard();
  await userEvent.click(screen.getByRole('button', { name: 'Analiz başlat' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('zaten aktif');
  expect(screen.queryByTestId('run-route')).not.toBeInTheDocument();
});

test('gönderim sürerken çift tıklama ikinci kayıt oluşturmaz', async () => {
  let release!: (r: Response) => void;
  vi.mocked(fetch).mockImplementationOnce(() => new Promise<Response>((r) => (release = r)));
  renderCard();
  await userEvent.click(screen.getByRole('button', { name: 'Analiz başlat' }));
  const busy = await screen.findByRole('button', { name: 'Oluşturuluyor…' });
  expect(busy).toBeDisabled();
  await userEvent.click(busy);
  expect(vi.mocked(fetch).mock.calls.filter(([u]) => String(u).endsWith('/api/analysis-runs/'))).toHaveLength(1);
  release(new Response(JSON.stringify({ detail: 'x' }), { status: 500, headers: { 'content-type': 'application/json' } }));
  expect(await screen.findByRole('alert')).toHaveTextContent(/beklenmeyen/i);
});
