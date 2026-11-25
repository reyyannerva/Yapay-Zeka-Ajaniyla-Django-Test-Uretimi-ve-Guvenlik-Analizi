import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Navigate, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, test, vi } from 'vitest';

import { resetMockProjects } from '../../lib/api/mock';
import { ROUTER_FUTURE } from '../../test/router-future';
import { Overview } from '../dashboard/Overview';
import { AnalysisLayout } from './AnalysisLayout';
import { AnalysisList } from './AnalysisList';
import { EndpointsPage } from './EndpointsPage';
import { FindingsPage } from './FindingsPage';
import { GeneratedTestsPage } from './GeneratedTestsPage';
import { ReportPage } from './ReportPage';
import { ResultsPage } from './ResultsPage';

afterEach(() => {
  resetMockProjects();
  vi.useRealTimers();
  vi.restoreAllMocks();
});

function renderAt(path: string, opts: { intervalMs?: number } = {}) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]} future={ROUTER_FUTURE}>
        <Routes>
          <Route path="/dashboard" element={<Overview />} />
          <Route path="/analyses" element={<AnalysisList />} />
          <Route path="/analyses/:id" element={<AnalysisLayout />}>
            <Route index element={<Navigate to="endpoints" replace />} />
            <Route path="endpoints" element={<EndpointsPage />} />
            <Route path="tests" element={<GeneratedTestsPage />} />
            <Route path="results" element={<ResultsPage intervalMs={opts.intervalMs ?? 50} />} />
            <Route path="findings" element={<FindingsPage />} />
            <Route path="report" element={<ReportPage delayMs={0} />} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('yönlendirme ve düzen', () => {
  test('analiz listesi DEMO analizleri bağlantı olarak gösterir ve proje filtresi uygular', async () => {
    renderAt('/analyses?project=2');
    const table = await screen.findByRole('table');
    expect(within(table).getByRole('link', { name: '#4' })).toHaveAttribute('href', '/analyses/4');
    expect(within(table).queryByRole('link', { name: '#1' })).not.toBeInTheDocument();
  });

  test('genel bakıştaki analiz numarası detay sayfasına götürür', async () => {
    renderAt('/dashboard');
    await userEvent.click(await screen.findByRole('link', { name: '#4' }));
    expect(await screen.findByRole('heading', { name: 'Analiz #4' })).toBeInTheDocument();
    expect(await screen.findByRole('region', { name: 'Kaynak kod analizi' })).toBeInTheDocument();
  });

  test('sekmeler arasında gezinilir; DEMO etiketi görünür', async () => {
    renderAt('/analyses/4');
    await screen.findByRole('heading', { name: 'Analiz #4' });
    expect(screen.getAllByText(/DEMO/).length).toBeGreaterThan(0);
    const tabs = screen.getByRole('navigation', { name: 'Analiz bölümleri' });
    await userEvent.click(within(tabs).getByRole('link', { name: 'Güvenlik bulguları' }));
    expect(await screen.findByRole('region', { name: 'Güvenlik bulguları' })).toBeInTheDocument();
    await userEvent.click(within(tabs).getByRole('link', { name: 'Üretilen testler' }));
    expect(await screen.findByRole('region', { name: 'Otomatik Pytest üretimi' })).toBeInTheDocument();
  });

  test.each(['/analyses/abc', '/analyses/999'])('%s için "Analiz bulunamadı" gösterilir', async (path) => {
    renderAt(path);
    expect(await screen.findByText('Analiz bulunamadı')).toBeInTheDocument();
  });

  test('analiz aşaması (AnalysisRun) test durumlarından ayrı gösterilir', async () => {
    renderAt('/analyses/6/endpoints');
    expect(await screen.findByRole('list', { name: 'Analiz aşamaları' })).toBeInTheDocument();
    expect(screen.getAllByText(/SANDBOX|sandbox/).length).toBeGreaterThan(0);
  });
});

describe('kaynak kod analizi', () => {
  test('metot filtresi, arama, kimlik doğrulama filtresi ve temizleme', async () => {
    renderAt('/analyses/4/endpoints');
    const region = await screen.findByRole('region', { name: 'Kaynak kod analizi' });
    const methods = within(region).getByRole('group', { name: 'HTTP metodu' });
    expect(within(region).getByText('10 / 10 endpoint gösteriliyor')).toBeInTheDocument();

    await userEvent.click(within(methods).getByRole('button', { name: /^DELETE/ }));
    expect(within(methods).getByRole('button', { name: /^DELETE/ })).toHaveAttribute('aria-pressed', 'true');
    expect(within(region).getByText('1 / 10 endpoint gösteriliyor')).toBeInTheDocument();

    await userEvent.click(within(methods).getByRole('button', { name: /^GET/ }));
    expect(within(region).getByText('7 / 10 endpoint gösteriliyor')).toBeInTheDocument();

    await userEvent.click(within(region).getAllByRole('button', { name: 'Filtreleri temizle' })[0]!);
    await userEvent.selectOptions(within(region).getByLabelText('Kimlik doğrulama'), 'unknown');
    expect(within(region).getByText('1 / 10 endpoint gösteriliyor')).toBeInTheDocument();
    expect(within(region).getByText('/api/products/')).toBeInTheDocument();
  });

  test('eşleşme yoksa boş filtre durumu ve temizleme eylemi', async () => {
    renderAt('/analyses/4/endpoints');
    const region = await screen.findByRole('region', { name: 'Kaynak kod analizi' });
    await userEvent.type(within(region).getByLabelText('Endpoint veya view ara'), 'olmayan-yol');
    expect(within(region).getByText('Filtrelerle eşleşen endpoint yok')).toBeInTheDocument();
    const clears = within(region).getAllByRole('button', { name: 'Filtreleri temizle' });
    await userEvent.click(clears[clears.length - 1]!);
    expect(within(region).getByText('10 / 10 endpoint gösteriliyor')).toBeInTheDocument();
  });

  test('analiz öncesi boş durum', async () => {
    renderAt('/analyses/3/endpoints');
    expect(await screen.findByText('Kaynak kod analizi henüz tamamlanmadı')).toBeInTheDocument();
  });
});

describe('Pytest üretimi', () => {
  test('kural tabanlı ve LLM testleri ayrılır; fallback ve doğrulama bilgisi gösterilir', async () => {
    renderAt('/analyses/4/tests');
    const region = await screen.findByRole('region', { name: 'Otomatik Pytest üretimi' });
    const list = within(region).getByRole('list', { name: 'Üretilen testler' });
    const first = within(list).getAllByRole('button')[0]!;
    expect(first).toHaveTextContent('test_order_list_requires_auth');
    expect(within(region).getByTestId('model-info')).toHaveTextContent('dil modeli kullanılmadı');
    expect(within(region).getByRole('button', { name: /kopyala/ })).toBeInTheDocument();

    await userEvent.click(within(region).getByRole('button', { name: 'LLM' }));
    const llmButtons = within(within(region).getByRole('list', { name: 'Üretilen testler' })).getAllByRole('button');
    const fallbackTest = llmButtons.find((b) => /tenant|other_user|başka|1042|long|cross/i.test(b.textContent ?? '')) ?? llmButtons[0]!;
    await userEvent.click(fallbackTest);
    const info = within(region).getByTestId('model-info');
    expect(info.textContent).toMatch(/Fallback kullanıldı|Sağlayıcı ve model bilgisi|Groq|Gemini/);
  });

  test('LLM testinde fallback bilgisi yalnızca metadata bildiriyorsa gösterilir', async () => {
    renderAt('/analyses/6/tests');
    const region = await screen.findByRole('region', { name: 'Otomatik Pytest üretimi' });
    expect(within(region).getByTestId('model-info')).toHaveTextContent('backend tarafından döndürülmedi');
    expect(within(region).queryByText('Fallback kullanıldı')).not.toBeInTheDocument();
  });
});

describe('güvenlik bulguları', () => {
  test('doğrulama sınıfı ve önem derecesi ayrı; VERIFIED başarı tonu almaz', async () => {
    renderAt('/analyses/4/findings');
    const region = await screen.findByRole('region', { name: 'Güvenlik bulguları' });
    const detail = within(region).getByRole('region', { name: 'Bulgu ayrıntısı' });
    expect(within(detail).getByText('Doğrulanmış')).not.toHaveAttribute('data-tone', 'pass');
    expect(detail.querySelector('[data-severity="HIGH"]')).not.toBeNull();
    expect(within(detail).getByText('Kanıt')).toBeInTheDocument();
    expect(within(detail).getByText(/Referans:/)).toBeInTheDocument();
  });

  test('sınıf filtresi ve kanıt/öneri olmayan bulgu', async () => {
    renderAt('/analyses/4/findings');
    const region = await screen.findByRole('region', { name: 'Güvenlik bulguları' });
    await userEvent.selectOptions(within(region).getByLabelText('Doğrulama sınıfı'), 'UNCERTAIN');
    const detail = within(region).getByRole('region', { name: 'Bulgu ayrıntısı' });
    expect(within(detail).getByText('Bu bulgu için kanıt kaydı bulunmuyor.')).toBeInTheDocument();
    expect(within(detail).getByText('Bu bulgu türü için kayıtlı bir düzeltme önerisi yok.')).toBeInTheDocument();
    expect(within(detail).getByText('Konum bilgisi yok')).toBeInTheDocument();
  });

  test('bulgu yoksa "güvenli" denmez', async () => {
    renderAt('/analyses/5/findings');
    expect(await screen.findByText('Güvenlik bulgusu bulunmadı')).toBeInTheDocument();
    expect(screen.getByText(/güvenli olduğu anlamına gelmez/)).toBeInTheDocument();
  });
});

describe('test sonuçları', () => {
  test('canlı ilerleme: tamamlanan/toplam, yüzde, tahmini süre ve canlı çıktı güncellenir', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    renderAt('/analyses/2/results', { intervalMs: 50 });
    const summary = await screen.findByTestId('progress-summary');
    expect(summary).toHaveTextContent('4 / 10 test tamamlandı · 1 çalışıyor · 5 bekliyor');
    expect(screen.getByTestId('progress-percent')).toHaveTextContent('%40');
    expect(screen.getByTestId('remaining-estimate')).toHaveTextContent(/tahmin; kesin bitiş zamanı değildir/);
    expect(screen.getByText(/DEMO akışı/)).toBeInTheDocument();
    const output = screen.getByRole('region', { name: 'Canlı test çıktısı' });
    expect(await within(output).findByText(/test_note_update_owner_ok başladı/)).toBeInTheDocument();

    await act(async () => {
      vi.advanceTimersByTime(50);
    });
    expect(screen.getByTestId('progress-summary')).toHaveTextContent('5 / 10 test tamamlandı');

    await act(async () => {
      vi.advanceTimersByTime(500);
    });
    expect(screen.getByTestId('progress-summary')).toHaveTextContent('10 / 10 test tamamlandı · 0 çalışıyor · 0 bekliyor');
    expect(screen.getByTestId('remaining-estimate')).toHaveTextContent('Kalan test yok');
    expect(screen.getByText('Akış tamamlandı')).toBeInTheDocument();
    expect(within(output).getByText(/note_factory/)).toBeInTheDocument();
  });

  test('sayfadan ayrılınca canlı akış zamanlayıcısı temizlenir', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const clearSpy = vi.spyOn(globalThis, 'clearInterval');
    const view = renderAt('/analyses/2/results', { intervalMs: 50 });
    await screen.findByTestId('progress-summary');
    view.unmount();
    expect(clearSpy).toHaveBeenCalled();
  });

  test('PASS, FAIL, ERROR, TIMEOUT ve NOT_RUN ayrı gösterilir; satır çıktısı açılır', async () => {
    renderAt('/analyses/4/results');
    const table = await screen.findByRole('table');
    for (const s of ['PASS', 'FAIL', 'ERROR', 'TIMEOUT', 'NOT_RUN']) {
      expect(table.querySelector(`[data-status="${s}"]`)).not.toBeNull();
    }
    await userEvent.click(screen.getByRole('button', { name: /^TIMEOUT/ }));
    const rows = within(screen.getByRole('table')).getAllByRole('row');
    expect(rows).toHaveLength(2);
    const testButton = within(rows[1]!).getAllByRole('button')[0]!;
    await userEvent.click(testButton);
    expect(testButton).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('Test durumu dağılımı')).toBeInTheDocument();
  });

  test('başarısız analizde kısmi sonuç uyarısı gösterilir', async () => {
    renderAt('/analyses/6/results');
    expect(await screen.findByText(/Kısmi sonuç: analiz tamamlanmadan durdu/)).toBeInTheDocument();
  });

  test('yürütme öncesi boş durum', async () => {
    renderAt('/analyses/3/results');
    expect(await screen.findByText('Testler henüz çalıştırılmadı')).toBeInTheDocument();
  });
});

describe('raporlama ve metrikler', () => {
  test('bölüm seçimi, boş seçim doğrulaması ve JSON hazırlama/indirme', async () => {
    const createUrl = vi.fn(() => 'blob:demo');
    const revokeUrl = vi.fn();
    Object.assign(URL, { createObjectURL: createUrl, revokeObjectURL: revokeUrl });
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});

    renderAt('/analyses/4/report');
    const region = await screen.findByRole('region', { name: 'Raporlama' });
    expect(within(region).getByTestId('selected-sections').querySelectorAll('li')).toHaveLength(3);

    await userEvent.click(within(region).getByRole('button', { name: 'Seçimi temizle' }));
    await userEvent.click(within(region).getByRole('button', { name: 'PDF raporu hazırla' }));
    expect(within(region).getByRole('alert')).toHaveTextContent('en az bir bölüm');

    await userEvent.click(within(region).getByRole('checkbox', { name: /Değerlendirme metrikleri/ }));
    await userEvent.click(within(region).getByLabelText('JSON'));
    await userEvent.click(within(region).getByRole('button', { name: 'JSON raporu hazırla' }));
    const ready = await within(region).findByTestId('report-ready');
    expect(ready).toHaveTextContent('tam · 1 bölüm');
    await userEvent.click(within(ready).getByRole('button', { name: 'JSON indir (DEMO)' }));
    expect(createUrl).toHaveBeenCalledTimes(1);
    expect(click).toHaveBeenCalledTimes(1);
    expect(revokeUrl).toHaveBeenCalledWith('blob:demo');
    expect(within(ready).getByRole('status')).toHaveTextContent('İndirme başarılı: testkalkan-analiz-4-rapor-demo.json');
  });

  test('PDF hazır olduğunda sahte PDF üretilmez', async () => {
    renderAt('/analyses/4/report');
    const region = await screen.findByRole('region', { name: 'Raporlama' });
    fireEvent.click(within(region).getByRole('button', { name: 'PDF raporu hazırla' }));
    const ready = await within(region).findByTestId('report-ready');
    // İndirme arayüzü vardır ancak sahte PDF üretmemek için düğme pasiftir.
    expect(within(ready).getByRole('button', { name: 'PDF indir' })).toBeDisabled();
    expect(ready).toHaveTextContent(/backend rapor servisiyle/);
  });

  test('rapor hatası ve kısmi kapsam', async () => {
    renderAt('/analyses/6/report');
    const region = await screen.findByRole('region', { name: 'Raporlama' });
    expect(within(region).getByText(/kısmi \(PARTIAL\)/)).toBeInTheDocument();
    await userEvent.click(within(region).getByRole('button', { name: 'PDF raporu hazırla' }));
    await waitFor(() => expect(within(region).getByRole('alert')).toHaveTextContent('DEMO hata senaryosu'));
  });

  test('ground truth yoksa metrik üretilmez ve metrik bölümü seçilemez', async () => {
    renderAt('/analyses/5/report');
    const region = await screen.findByRole('region', { name: 'Raporlama' });
    expect(within(region).getByTestId('no-ground-truth')).toBeInTheDocument();
    expect(within(region).getByRole('checkbox', { name: /Değerlendirme metrikleri/ })).toBeDisabled();
    expect(within(region).queryByText('Precision')).not.toBeInTheDocument();
  });

  test('metrikler TP/FP/FN ile hesaplanır ve PASS/FAIL ile karışmaz', async () => {
    renderAt('/analyses/4/report');
    const metrics = await screen.findByRole('region', { name: 'Değerlendirme metrikleri' });
    expect(within(metrics).getByText('TP (doğru pozitif)')).toBeInTheDocument();
    expect(within(metrics).getAllByText('0,75').length).toBe(3);
    expect(within(metrics).queryByText('PASS')).not.toBeInTheDocument();
    expect(screen.getByText('Güvenlik tespit metrikleri')).toBeInTheDocument();
  });

  test('yürütme sürerken rapor hazırlanamaz', async () => {
    renderAt('/analyses/2/report');
    expect(await screen.findByText('Rapor henüz hazırlanamaz')).toBeInTheDocument();
  });

  test('veri yoksa "veri bulunmuyor" durumu', async () => {
    renderAt('/analyses/1/report');
    expect(await screen.findByText('Rapora konacak veri bulunmuyor')).toBeInTheDocument();
  });
});
