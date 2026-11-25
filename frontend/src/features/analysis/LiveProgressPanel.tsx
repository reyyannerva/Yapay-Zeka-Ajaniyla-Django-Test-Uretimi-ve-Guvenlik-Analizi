import { Card } from '../../components/ui/Card';
import { MetricCard } from '../../components/ui/MetricCard';
import {
  computeProgress,
  estimateRemaining,
  formatDuration,
  formatPercent,
  isTerminalTestStatus,
} from '../../lib/execution-progress';
import type { GeneratedTest, TestExecutionResult } from '../../types';

export interface LiveProgressPanelProps {
  results: readonly TestExecutionResult[];
  tests: readonly GeneratedTest[];
  live: boolean;
}

/** Test bazında yürütme ilerlemesi (analiz aşamasından ayrı). */
export function LiveProgressPanel({ results, tests, live }: LiveProgressPanelProps) {
  const progress = computeProgress(results.map((r) => r.status));
  const timed = results.filter((r) => isTerminalTestStatus(r.status) && r.duration_ms !== null);
  const estimate = estimateRemaining({
    completedDurationMsTotal: timed.reduce((sum, r) => sum + (r.duration_ms ?? 0), 0),
    completedWithDuration: timed.length,
    remaining: progress.running + progress.pending,
  });
  const active = results
    .filter((r) => r.status === 'RUNNING')
    .map((r) => tests.find((t) => t.id === r.generated_test)?.test_name ?? `Test ${r.generated_test}`);

  return (
    <Card className="flex flex-col gap-4" role="region" aria-label="Test yürütme ilerlemesi">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-display text-lg font-semibold text-fg">Test yürütme ilerlemesi</h2>
        {live ? (
          <span className="inline-flex items-center gap-2 text-xs font-medium text-process">
            <span aria-hidden="true" className="h-2 w-2 animate-pulse rounded-full bg-process motion-reduce:animate-none" />
            Canlı · DEMO akışı (gerçek sandbox bağlantısı değil)
          </span>
        ) : (
          <span className="text-xs text-muted">Akış tamamlandı</span>
        )}
      </div>
      <div className="flex items-center gap-3">
        <div
          role="progressbar"
          aria-label="Tamamlanan testler"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={progress.percent ?? undefined}
          aria-valuetext={progress.percent === null ? 'Henüz test yok' : `${progress.completed} / ${progress.total} test tamamlandı`}
          className="h-2 flex-1 overflow-hidden rounded-full bg-surface-2"
        >
          <div className="h-full rounded-full bg-process" style={{ width: `${progress.percent ?? 0}%` }} />
        </div>
        <span className="font-mono text-sm font-semibold text-fg" data-testid="progress-percent">
          {formatPercent(progress.percent)}
        </span>
      </div>
      <p className="text-sm text-fg" data-testid="progress-summary">
        {`${progress.completed} / ${progress.total} test tamamlandı · ${progress.running} çalışıyor · ${progress.pending} bekliyor`}
      </p>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <MetricCard label="PASS" value={progress.byStatus.PASS} />
        <MetricCard label="FAIL" value={progress.byStatus.FAIL} />
        <MetricCard label="ERROR" value={progress.byStatus.ERROR} />
        <MetricCard label="TIMEOUT" value={progress.byStatus.TIMEOUT} />
        <MetricCard label="RUNNING" value={progress.byStatus.RUNNING} />
        <MetricCard label="PENDING" value={progress.byStatus.PENDING} />
      </div>
      <dl className="grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-xs text-muted">Çalışan test</dt>
          <dd className="break-all font-mono text-xs text-fg">{active.length > 0 ? active.join(', ') : '—'}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Tahmini kalan süre</dt>
          <dd className="text-fg" data-testid="remaining-estimate">
            {estimate.kind === 'estimate'
              ? `yaklaşık ${formatDuration(estimate.ms)} (tahmin; kesin bitiş zamanı değildir)`
              : estimate.kind === 'done'
                ? 'Kalan test yok'
                : `Belirsiz — ${estimate.reason}`}
          </dd>
        </div>
      </dl>
    </Card>
  );
}
