import { Link } from 'react-router-dom';

import { Card } from '../../components/ui/Card';
import { DataTable } from '../../components/ui/DataTable';
import type { DataTableColumn } from '../../components/ui/DataTable';
import { EmptyState } from '../../components/ui/EmptyState';
import { MetricCard } from '../../components/ui/MetricCard';
import { Spinner } from '../../components/ui/Spinner';
import { StageStrip } from '../../components/ui/StageStrip';
import { FindingBadge, StatusBadge } from '../../components/ui/StatusBadge';
import type { AnalysisRun, LlmProvider } from '../../types';
import { SAMPLE_FINDINGS_BY_RUN, useOverviewData } from './useOverviewData';

// Yalnızca sağlayıcı gösterilir; spesifik model kimliği sabitmiş gibi yazılmaz.
const PROVIDER_LABEL: Record<LlmProvider, string> = {
  GROQ: 'Groq',
  GEMINI: 'Gemini',
  OLLAMA: 'Ollama',
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('tr-TR', { dateStyle: 'medium', timeZone: 'UTC' });
}

const COLUMNS: readonly DataTableColumn<AnalysisRun>[] = [
  { key: 'id', header: 'Analiz', cell: (run) => (
      <Link to={`/analyses/${run.id}`} className="font-mono text-accent hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent">
        {`#${run.id}`}
      </Link>
    ),
  },
  { key: 'project', header: 'Proje', cell: (run) => `Proje ${run.project}` },
  { key: 'status', header: 'Durum', cell: (run) => <StatusBadge status={run.status} /> },
  {
    key: 'llm',
    header: 'LLM sağlayıcı',
    cell: (run) => (run.llm_provider ? PROVIDER_LABEL[run.llm_provider] : '—'),
  },
  {
    key: 'finding',
    header: 'Güvenlik bulgusu (örnek)',
    cell: (run) => {
      const finding = SAMPLE_FINDINGS_BY_RUN[run.id];
      return finding ? (
        <FindingBadge classification={finding.classification} severity={finding.severity} />
      ) : (
        '—'
      );
    },
  },
  { key: 'created', header: 'Tarih', cell: (run) => formatDate(run.created_at) },
];

export function Overview() {
  const { isLoading, isError, metrics, recentRuns, activeRuns } = useOverviewData();

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1">
        <p className="font-mono text-xs uppercase tracking-[0.12em] text-accent">Panel</p>
        <h1 className="font-display text-2xl font-semibold text-fg">Genel bakış</h1>
        <p className="text-sm text-muted">
          Örnek veri: değerler gerçek bir analiz sonucunu temsil etmez.
        </p>
      </header>

      {isLoading ? (
        <Spinner />
      ) : isError || !metrics ? (
        <EmptyState title="Veriler alınamadı" description="Lütfen daha sonra tekrar deneyin." />
      ) : (
        <>
          <section aria-label="Metrikler" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard label="Toplam proje" value={metrics.projectCount} hint="Örnek veri" />
            <MetricCard label="Toplam analiz" value={metrics.runCount} hint="Örnek veri" />
            <MetricCard
              label="Devam eden analiz"
              value={metrics.inProgressCount}
              hint="Örnek veri"
            />
            <MetricCard
              label="Doğrulanmış bulgu"
              value={metrics.verifiedFindingCount}
              hint="Örnek veri"
              alert={metrics.verifiedFindingCount > 0}
            />
          </section>

          {activeRuns.length > 0 ? (
            <section aria-label="Devam eden analizler" className="flex flex-col gap-3">
              <h2 className="font-display text-lg font-semibold text-fg">Devam eden analizler</h2>
              {activeRuns.map((run) => (
                <Card key={run.id} className="flex flex-col gap-4">
                  <div className="flex flex-wrap items-center gap-3 border-b border-border pb-3">
                    <h3 className="font-mono text-base font-semibold text-fg">{`Proje ${run.project}`}</h3>
                    <StatusBadge status={run.status} />
                    <span className="ml-auto text-xs text-muted">
                      {run.llm_provider ? PROVIDER_LABEL[run.llm_provider] : 'Kural tabanlı'} · analiz #
                      {run.id}
                    </span>
                  </div>
                  <StageStrip status={run.status} progress={run.progress} />
                </Card>
              ))}
            </section>
          ) : null}

          <section aria-label="Son analizler" className="flex flex-col gap-3">
            <h2 className="font-display text-lg font-semibold text-fg">Son analizler</h2>
            <DataTable
              columns={COLUMNS}
              rows={recentRuns}
              rowKey={(run) => run.id}
              emptyState={
                <EmptyState
                  title="Henüz analiz yok"
                  description="Bir proje seçip analiz başlattığınızda burada listelenir."
                />
              }
            />
          </section>
        </>
      )}
    </div>
  );
}
