import { Fragment, useMemo, useState } from 'react';

import { CodeBlock } from '../../components/ui/CodeBlock';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { HttpMethodBadge } from '../../components/ui/HttpMethodBadge';
import { Spinner } from '../../components/ui/Spinner';
import { TestStatusIndicator } from '../../components/ui/TestStatusIndicator';
import { ERROR_ORIGIN_LABEL, ERROR_TYPE_LABEL } from '../../lib/analysis-labels';
import { computeProgress, formatDuration } from '../../lib/execution-progress';
import type { AnalysisRunStatus, TestExecutionStatus } from '../../types';
import { TestStatusChart } from './charts';
import { LiveOutput } from './LiveOutput';
import { LiveProgressPanel } from './LiveProgressPanel';
import { useAnalysisContext, useEndpoints, useExecutionStream, useGeneratedTests } from './useAnalysisData';

type StatusFilter = 'ALL' | TestExecutionStatus;
const FILTERS: readonly TestExecutionStatus[] = ['PASS', 'FAIL', 'ERROR', 'TIMEOUT', 'RUNNING', 'PENDING', 'NOT_RUN', 'STOPPED'];
const NOT_EXECUTED_YET: readonly AnalysisRunStatus[] = ['QUEUED', 'ANALYZING', 'GENERATING', 'VALIDATING'];

export function ResultsPage({ intervalMs }: { intervalMs?: number }) {
  const { run } = useAnalysisContext();
  const stream = useExecutionStream(run.id, intervalMs);
  const tests = useGeneratedTests(run.id);
  const endpoints = useEndpoints(run.id);
  const [filter, setFilter] = useState<StatusFilter>('ALL');
  const [openId, setOpenId] = useState<number | null>(null);

  const results = stream.status === 'ready' ? stream.snapshot.results : [];
  const progress = useMemo(() => computeProgress(results.map((r) => r.status)), [results]);
  const visible = results.filter((r) => filter === 'ALL' || r.status === filter);

  if (stream.status === 'loading' || tests.isLoading) return <Spinner label="Test sonuçları yükleniyor" />;
  if (stream.status === 'error' || tests.isError) {
    return <ErrorState title="Test sonuçları alınamadı" description="Lütfen sayfayı yenileyip tekrar deneyin." />;
  }
  if (results.length === 0) {
    return NOT_EXECUTED_YET.includes(run.status) ? (
      <EmptyState title="Testler henüz çalıştırılmadı" description="Test yürütme aşaması başlayınca sonuçlar burada canlı olarak görünür." />
    ) : (
      <EmptyState title="Test sonucu yok" description="Bu analizde çalıştırılan test bulunmuyor." />
    );
  }

  const testList = tests.data ?? [];
  const testOf = (id: number) => testList.find((t) => t.id === id);
  const endpointOf = (testId: number) => endpoints.data?.find((e) => e.id === testOf(testId)?.endpoint);
  const partial = (run.status === 'FAILED' || run.status === 'CANCELLED') && (progress.byStatus.NOT_RUN > 0 || progress.byStatus.STOPPED > 0);
  const live = !stream.snapshot.finished;

  return (
    <section aria-label="Test sonuçları" className="flex flex-col gap-4">
      {partial ? (
        <p role="note" className="rounded-md border border-fail bg-fail-bg px-3 py-2 text-sm text-fg">
          Kısmi sonuç: analiz tamamlanmadan durdu. Çalıştırılmayan testler NOT_RUN/STOPPED olarak gösterilir; sonuçlar tam analiz sonucu değildir.
        </p>
      ) : null}
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
        <LiveProgressPanel results={results} tests={testList} live={live} />
        <TestStatusChart counts={progress.byStatus} />
      </div>
      <LiveOutput results={results} tests={testList} />

      <div className="flex flex-wrap gap-2" role="group" aria-label="Duruma göre filtre">
        {(['ALL', ...FILTERS.filter((s) => progress.byStatus[s] > 0 || ['PASS', 'FAIL', 'ERROR', 'TIMEOUT'].includes(s))] as StatusFilter[]).map((s) => (
          <button
            key={s}
            type="button"
            aria-pressed={filter === s}
            onClick={() => setFilter(s)}
            className={`rounded-md border px-2.5 py-1 font-mono text-xs focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent ${
              filter === s ? 'border-accent bg-accent-soft font-semibold text-accent' : 'border-border-strong text-fg hover:bg-surface-2'
            }`}
          >
            {s === 'ALL' ? `Tümü ${results.length}` : `${s} ${progress.byStatus[s]}`}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto rounded-lg border border-border bg-surface">
        <table className="w-full min-w-[760px] border-collapse text-left text-sm">
          <thead className="bg-surface-2 text-xs text-muted">
            <tr>
              <th scope="col" className="border-b border-border px-4 py-2 font-medium">Test</th>
              <th scope="col" className="border-b border-border px-4 py-2 font-medium">Endpoint</th>
              <th scope="col" className="border-b border-border px-4 py-2 font-medium">Durum</th>
              <th scope="col" className="border-b border-border px-4 py-2 font-medium">Beklenen / gözlenen</th>
              <th scope="col" className="border-b border-border px-4 py-2 font-medium">Süre</th>
              <th scope="col" className="border-b border-border px-4 py-2 font-medium">Özet</th>
            </tr>
          </thead>
          <tbody>
            {visible.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-sm text-muted">Bu durumda test yok.</td>
              </tr>
            ) : (
              visible.map((r) => {
                const t = testOf(r.generated_test);
                const ep = endpointOf(r.generated_test);
                const open = openId === r.id;
                return (
                  <Fragment key={r.id}>
                    <tr className="border-b border-border align-top">
                      <td className="max-w-[20rem] px-4 py-2">
                        <button
                          type="button"
                          aria-expanded={open}
                          onClick={() => setOpenId(open ? null : r.id)}
                          className="break-all text-left font-mono text-xs font-medium text-fg hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
                        >
                          {t?.test_name ?? `Test ${r.generated_test}`}
                        </button>
                      </td>
                      <td className="px-4 py-2">
                        {ep ? (
                          <span className="flex flex-wrap items-center gap-2">
                            <HttpMethodBadge method={ep.http_method} />
                            <code className="break-all font-mono text-xs">{ep.path}</code>
                          </span>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td className="px-4 py-2"><TestStatusIndicator status={r.status} /></td>
                      <td className="px-4 py-2 font-mono text-xs">
                        {`${t?.expected_status ?? '—'} / `}
                        <span className={r.status === 'FAIL' ? 'font-semibold text-error' : ''}>{r.observed_status ?? '—'}</span>
                      </td>
                      <td className="whitespace-nowrap px-4 py-2 font-mono text-xs text-muted">{formatDuration(r.duration_ms)}</td>
                      <td className="max-w-[18rem] px-4 py-2 text-xs text-muted">
                        <span className="break-words">{r.error_summary || '—'}</span>
                        {r.error_type ? (
                          <span className="block">{`${ERROR_TYPE_LABEL[r.error_type]}${r.error_origin ? ` · ${ERROR_ORIGIN_LABEL[r.error_origin]}` : ''}`}</span>
                        ) : null}
                      </td>
                    </tr>
                    {open ? (
                      <tr className="border-b border-border">
                        <td colSpan={6} className="bg-surface-2 px-4 py-3">
                          {r.output_excerpt ? (
                            <CodeBlock code={r.output_excerpt} label={`${t?.test_name ?? 'Test'} çıktısı`} maxHeightClass="max-h-64" />
                          ) : (
                            <p className="text-sm text-muted">Bu test için çıktı kaydı yok.</p>
                          )}
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-muted">
        Test durumları (PASS/FAIL/ERROR/TIMEOUT) yürütme sonucudur; güvenlik tespit metrikleri (Precision/Recall/F1) bunlardan türetilmez.
      </p>
    </section>
  );
}
