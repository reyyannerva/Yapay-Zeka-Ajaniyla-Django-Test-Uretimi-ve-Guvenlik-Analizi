import { Card } from '../../components/ui/Card';
import { MetricCard } from '../../components/ui/MetricCard';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { PROVIDER_LABEL } from '../../lib/analysis-labels';
import { formatDate } from '../projects/ProjectValidationBadge';
import { useAnalysisContext } from './useAnalysisData';

/**
 * Gerçek analiz kaydının özeti (H5-03 / #41). Yalnızca backend'in döndürdüğü alanlar gösterilir.
 * Analiz oluşturma bu sürümde yalnızca QUEUED bir kayıt açar; analiz motoru otomatik tetiklenmez.
 */
export function RunSummaryPage() {
  const { run } = useAnalysisContext();
  const snapshot = run.requirements_snapshot;
  const percent = run.progress.percent;

  return (
    <section aria-label="Analiz özeti" className="flex flex-col gap-4">
      {run.status === 'QUEUED' ? (
        <p role="note" className="rounded-md border border-process bg-process-bg p-3 text-sm text-fg">
          Analiz kaydı oluşturuldu ve kuyrukta bekliyor. Bu sürümde analiz motoru (AST, test üretimi, sandbox,
          güvenlik taraması) otomatik başlatılmaz; durum backend tarafından güncellendikçe bu sayfa yenilenir.
        </p>
      ) : null}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <MetricCard label="Durum" value={<StatusBadge status={run.status} />} />
        <MetricCard label="Üretilen test" value={run.generated_test_count} />
        <MetricCard
          label="Test yürütme ilerlemesi"
          value={percent === null ? '—' : `%${percent.toLocaleString('tr-TR')}`}
          hint={percent === null ? 'Henüz yürütme kaydı yok' : `${run.progress.completed} / ${run.progress.total} test`}
        />
        <MetricCard
          label="Kapsam"
          value={run.coverage_percent === null ? '—' : `%${Number(run.coverage_percent).toLocaleString('tr-TR')}`}
          hint={run.coverage_percent === null ? 'Henüz ölçülmedi' : undefined}
        />
      </div>

      <Card className="flex flex-col gap-4">
        <h2 className="font-display text-lg font-semibold text-fg">Kayıt bilgileri</h2>
        <dl className="grid gap-3 sm:grid-cols-2">
          <div>
            <dt className="text-xs text-muted">Oluşturulma</dt>
            <dd className="text-sm text-fg">{formatDate(run.created_at)}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Bitiş</dt>
            <dd className="text-sm text-fg">{run.finished_at ? formatDate(run.finished_at) : 'Henüz bitmedi'}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Model</dt>
            <dd className="text-sm text-fg">
              {run.llm_provider ? (
                <>
                  {PROVIDER_LABEL[run.llm_provider]} · <code className="font-mono text-xs">{run.llm_model}</code>
                </>
              ) : (
                'Kural tabanlı (dil modeli kullanılmaz)'
              )}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Görev kimliği</dt>
            <dd className="text-sm text-fg">{run.celery_task_id ? <code className="font-mono text-xs">{run.celery_task_id}</code> : 'Atanmadı'}</dd>
          </div>
        </dl>
        {run.error_code ? (
          <p role="alert" className="rounded-md border border-error bg-error-bg p-3 text-sm">
            <strong className="font-semibold">{run.error_code}</strong>
            {run.error_message ? ` — ${run.error_message}` : ''}
          </p>
        ) : null}
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-display text-lg font-semibold text-fg">Referans gereksinim anlık görüntüsü</h2>
        <p className="text-sm text-muted">
          Analiz oluşturulduğu anda projenin etkin referans gereksinimleri bu kayda kopyalanır.
        </p>
        {snapshot.length === 0 ? (
          <p className="text-sm text-muted">Analiz oluşturulduğunda projede etkin referans gereksinim yoktu.</p>
        ) : (
          <ul className="flex flex-col gap-1 text-sm" aria-label="Anlık görüntüdeki gereksinimler">
            {snapshot.map((item, index) => (
              <li key={String(item.id ?? index)} className="flex flex-wrap items-center gap-2">
                <code className="font-mono text-xs">{String(item.requirement_code ?? '—')}</code>
                <span className="text-muted">{String(item.category ?? '')}</span>
                <span>{String(item.title ?? '')}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </section>
  );
}
