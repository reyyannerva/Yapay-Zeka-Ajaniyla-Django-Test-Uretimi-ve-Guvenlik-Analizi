import { Card } from '../../components/ui/Card';
import { formatMetric, summarize } from '../../lib/evaluation-metrics';
import type { EvaluationCounts } from '../../types';
import { MetricsChart } from './charts';

/**
 * Güvenlik tespit değerlendirmesi (TP/FP/FN → Precision/Recall/F1). Test yürütme sonuçlarından
 * (PASS/FAIL/ERROR/TIMEOUT) ayrı bir bileşendir ve yalnızca altın etiketli referans verisi varken
 * metrik gösterir.
 */
export function EvaluationPanel({ evaluation }: { evaluation: EvaluationCounts | null }) {
  if (!evaluation) {
    return (
      <Card className="flex flex-col gap-2" role="region" aria-label="Değerlendirme metrikleri">
        <h2 className="font-display text-lg font-semibold text-fg">Değerlendirme metrikleri</h2>
        <p className="text-sm text-muted" data-testid="no-ground-truth">
          Bu analiz için altın etiketli referans (ground truth) verisi yok; Precision, Recall ve F1 üretilmez.
        </p>
      </Card>
    );
  }
  const s = summarize(evaluation);
  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
      <Card className="flex flex-col gap-4" role="region" aria-label="Değerlendirme metrikleri">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="font-display text-lg font-semibold text-fg">Değerlendirme metrikleri</h2>
          <span className="rounded border border-fail bg-fail-bg px-1.5 py-0.5 font-mono text-[11px] font-semibold text-fail">DEMO</span>
        </div>
        <p className="text-xs text-muted">{`Kaynak: ${evaluation.ground_truth}. Test PASS/FAIL sayılarından türetilmez.`}</p>
        <dl className="grid grid-cols-4 gap-2 text-center">
          {(['tp', 'fp', 'fn', 'tn'] as const).map((k) => (
            <div key={k} className="rounded-md border border-border px-2 py-2">
              <dt className="font-mono text-xs text-muted">{k.toUpperCase()}</dt>
              <dd className="font-display text-xl font-semibold text-fg">{evaluation[k]}</dd>
            </div>
          ))}
        </dl>
        <dl className="grid grid-cols-3 gap-2 text-center">
          {[
            ['Precision', s.precision, 'TP / (TP + FP)'],
            ['Recall', s.recall, 'TP / (TP + FN)'],
            ['F1', s.f1, '2PR / (P + R)'],
          ].map(([label, value, formula]) => (
            <div key={label as string} className="rounded-md border border-border px-2 py-2">
              <dt className="text-xs text-muted">{label as string}</dt>
              <dd className="font-mono text-lg font-semibold text-fg">{formatMetric(value as number | null)}</dd>
              <dd className="font-mono text-[10px] text-muted">{formula as string}</dd>
            </div>
          ))}
        </dl>
      </Card>
      <MetricsChart summary={s} />
    </div>
  );
}
