import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, test } from 'vitest';

import { ToastProvider } from '../../components/ui/Toast';
import { fakeCalls, seedRequirement } from '../../test/fake-api';
import { ReferenceRequirementsCard } from './ReferenceRequirementsCard';

function renderCard(projectId = 1) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ToastProvider>
        <ReferenceRequirementsCard projectId={projectId} />
      </ToastProvider>
    </QueryClientProvider>,
  );
}

const VALID = JSON.stringify([
  {
    requirement_code: 'ACC-1',
    category: 'ACCESS_RULE',
    title: 'Anonim erişemez',
    expected_result: '401',
    specification: { schema_version: 1, endpoint: '/api/x/', method: 'delete', expected_status_by_role: { anonim: 401 } },
  },
]);

async function typeJson(text: string) {
  await userEvent.click(screen.getByRole('button', { name: 'JSON yükle' }));
  fireEvent.change(screen.getByLabelText(/JSON \(tek nesne/), { target: { value: text } });
  await userEvent.click(screen.getByRole('button', { name: 'Doğrula ve kaydet' }));
}

const writes = (method: string) => fakeCalls().filter((c) => c.method === method && c.path.startsWith('/api/reference-requirements/'));

test('yalnızca açık projenin kayıtları listelenir; boş durum gösterilir', async () => {
  seedRequirement({ project: 2, requirement_code: 'BASKA-PROJE' });
  renderCard(1);
  expect(await screen.findByText('Bu proje için referans gereksinim yok.')).toBeInTheDocument();
  expect(screen.queryByText('BASKA-PROJE')).not.toBeInTheDocument();
});

test('geçerli JSON POST ile kaydedilir (metot normalize edilir) ve listede görünür', async () => {
  renderCard(1);
  await screen.findByText('Bu proje için referans gereksinim yok.');
  await typeJson(VALID);
  const region = screen.getByRole('region', { name: 'Referans gereksinimler' });
  expect(await within(region).findByText('ACC-1')).toBeInTheDocument();
  expect(within(region).getByText('DELETE')).toBeInTheDocument();
  const body = JSON.parse(String(writes('POST')[0]!.body));
  expect(body).toMatchObject({ project: 1, source: 'JSON_UPLOAD', specification: { method: 'DELETE' } });
});

test('geçersiz JSON istemcide yakalanır ve hiçbir istek gönderilmez', async () => {
  renderCard(1);
  await screen.findByText('Bu proje için referans gereksinim yok.');
  await typeJson(VALID.replace('delete', 'TRACE'));
  expect(await screen.findByTestId('requirement-issues')).toHaveTextContent('specification.method');
  expect(screen.getByRole('alert')).toHaveTextContent('hiçbir kayıt gönderilmedi');
  expect(writes('POST')).toHaveLength(0);
});

test('sunucu doğrulama hatası (400) alan yoluyla gösterilir; sahte başarı yok', async () => {
  seedRequirement({ project: 1, requirement_code: 'ACC-1' });
  renderCard(1);
  await screen.findByText('ACC-1');
  await typeJson(VALID); // aynı kod → sunucu benzersizlik hatası
  expect(await screen.findByTestId('requirement-issues')).toHaveTextContent('non_field_errors');
  expect(screen.getByRole('alert')).toHaveTextContent('hiçbir kayıt kaydedilmedi');
});

test('düzenleme PUT, etkin/pasif PATCH, silme DELETE ile yapılır', async () => {
  seedRequirement({ project: 1, requirement_code: 'ROL-1', title: 'Eski başlık' });
  renderCard(1);
  await screen.findByText('ROL-1');

  await userEvent.click(screen.getByRole('button', { name: 'Düzenle' }));
  const editor = screen.getByLabelText(/JSON \(tek nesne/);
  fireEvent.change(editor, { target: { value: (editor as HTMLTextAreaElement).value.replace('Eski başlık', 'Yeni başlık') } });
  await userEvent.click(screen.getByRole('button', { name: 'Doğrula ve kaydet' }));
  expect(await screen.findByText('Yeni başlık')).toBeInTheDocument();
  expect(writes('PUT')).toHaveLength(1);
  expect(await screen.findByText('r2')).toBeInTheDocument();

  await userEvent.click(screen.getByRole('button', { name: 'Pasifleştir' }));
  expect(await screen.findByText('Pasif')).toBeInTheDocument();
  expect(JSON.parse(String(writes('PATCH')[0]!.body))).toEqual({ is_active: false });

  await userEvent.click(screen.getByRole('button', { name: 'Sil' }));
  await userEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Sil' }));
  expect(await screen.findByText('Bu proje için referans gereksinim yok.')).toBeInTheDocument();
  expect(writes('DELETE')).toHaveLength(1);
});

test('kayıt JSON olarak görüntülenebilir', async () => {
  seedRequirement({ project: 1, requirement_code: 'ROL-1' });
  renderCard(1);
  await userEvent.click(await screen.findByRole('button', { name: 'ROL-1' }));
  expect(screen.getByLabelText('ROL-1 JSON')).toHaveTextContent('"requirement_code": "ROL-1"');
});
