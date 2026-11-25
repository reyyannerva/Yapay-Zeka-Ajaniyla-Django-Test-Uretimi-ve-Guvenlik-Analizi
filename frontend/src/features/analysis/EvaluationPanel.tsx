import { Card } from '../../components/ui/Card';
import { MetricCard } from '../../components/ui/MetricCard';
import { Badge } from '../../components/ui/StatusBadge';
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
          <Badge tone="muted">DEMO</Badge>
        </div>
        <p className="text-xs text-muted">{`Kaynak: ${evaluation.ground_truth}. Test PASS/FAIL sayılarından türetilmez.`}</p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4" aria-label="Karşılaştırma sayımları">
          <MetricCard label="TP (doğru pozitif)" value={evaluation.tp} />
          <MetricCard label="FP (yanlış pozitif)" value={evaluation.fp} />
          <MetricCard label="FN (yanlış negatif)" value={evaluation.fn} />
          <MetricCard label="TN (doğru negatif)" value={evaluation.tn} />
        </div>
        <div className="grid gap-3 sm:grid-cols-3" aria-label="Metrikler">
          <MetricCard label="Precision" value={formatMetric(s.precision)} hint="TP / (TP + FP)" />
          <MetricCard label="Recall" value={formatMetric(s.recall)} hint="TP / (TP + FN)" />
          <MetricCard label="F1" value={formatMetric(s.f1)} hint="2PR / (P + R)" />
        </div>
      </Card>
      <MetricsChart summary={s} />
    </div>
  );
}
