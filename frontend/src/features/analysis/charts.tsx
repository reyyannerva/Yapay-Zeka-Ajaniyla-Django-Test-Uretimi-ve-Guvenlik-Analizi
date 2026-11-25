// Özet grafikleri (#40, Recharts). Renkler tema token'larından gelir (CSS değişkenleri).
// Her grafiğin yanında değerlerin metin karşılığı bulunur; veri yoksa grafik çizilmez.
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { SEVERITY_LABEL } from '../../lib/analysis-status';
import { formatMetric } from '../../lib/evaluation-metrics';
import type { EvaluationSummary } from '../../lib/evaluation-metrics';
import type { SecurityFinding, Severity, TestExecutionStatus } from '../../types';

interface Datum {
  key: string;
  label: string;
  value: number;
  color: string;
}

const TOOLTIP_STYLE = {
  background: 'var(--surface)',
  border: '1px solid var(--border-strong)',
  borderRadius: 6,
  color: 'var(--fg)',
  fontSize: 12,
};

function ChartFrame({
  title,
  data,
  emptyText,
  format = (v: number) => String(v),
  domain,
  footnote,
  slantedTicks = false,
}: {
  title: string;
  data: Datum[];
  emptyText: string;
  format?: (v: number) => string;
  domain?: [number, number];
  footnote?: string;
  /** Çok sayıda/uzun etiketlerde (dar ekran) eksen etiketlerini eğik yazar. */
  slantedTicks?: boolean;
}) {
  const hasData = data.some((d) => d.value > 0) || (domain !== undefined && data.length > 0);
  return (
    <figure className="flex min-w-0 flex-col gap-3 rounded-lg border border-border bg-surface p-4">
      <figcaption className="text-sm font-semibold text-fg">{title}</figcaption>
      {hasData ? (
        <>
          <div className="h-52 w-full min-w-0" aria-hidden="true">
            <ResponsiveContainer width="100%" height="100%" initialDimension={{ width: 480, height: 200 }}>
              <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
                <CartesianGrid vertical={false} stroke="var(--border)" />
                <XAxis
                  dataKey="label"
                  tick={{ fill: 'var(--muted)', fontSize: slantedTicks ? 10 : 11 }}
                  axisLine={{ stroke: 'var(--border-strong)' }}
                  tickLine={false}
                  interval={0}
                  angle={slantedTicks ? -35 : 0}
                  textAnchor={slantedTicks ? 'end' : 'middle'}
                  height={slantedTicks ? 52 : 30}
                />
                <YAxis
                  allowDecimals={domain !== undefined}
                  domain={domain ?? [0, 'auto']}
                  tick={{ fill: 'var(--muted)', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  cursor={{ fill: 'var(--surface-2)' }}
                  contentStyle={TOOLTIP_STYLE}
                  formatter={(v: number) => [format(v), 'Değer']}
                />
                <Bar dataKey="value" radius={[3, 3, 0, 0]} maxBarSize={44} isAnimationActive={false}>
                  {data.map((d) => (
                    <Cell key={d.key} fill={d.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <ul className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs sm:grid-cols-3" aria-label={`${title} değerleri`}>
            {data.map((d) => (
              <li key={d.key} className="flex items-center justify-between gap-2">
                <span className="inline-flex items-center gap-1.5 text-muted">
                  <span aria-hidden="true" className="h-2 w-2 rounded-sm" style={{ background: d.color }} />
                  {d.label}
                </span>
                <span className="font-mono font-semibold text-fg">{format(d.value)}</span>
              </li>
            ))}
          </ul>
          {footnote ? <p className="text-xs text-muted">{footnote}</p> : null}
        </>
      ) : (
        <p className="rounded-md border border-dashed border-border-strong px-3 py-6 text-center text-sm text-muted">{emptyText}</p>
      )}
    </figure>
  );
}

const STATUS_COLORS: Record<TestExecutionStatus, string> = {
  PASS: 'var(--pass)',
  FAIL: 'var(--fail)',
  ERROR: 'var(--error)',
  TIMEOUT: 'var(--timeout)',
  RUNNING: 'var(--process)',
  PENDING: 'var(--border-strong)',
  STOPPED: 'var(--muted)',
  NOT_RUN: 'var(--muted)',
};
const CORE_STATUSES: readonly TestExecutionStatus[] = ['PASS', 'FAIL', 'ERROR', 'TIMEOUT', 'RUNNING', 'PENDING'];

/** Test yürütme durumu dağılımı (PASS/FAIL/ERROR/TIMEOUT/RUNNING/PENDING; STOPPED/NOT_RUN varsa eklenir). */
export function TestStatusChart({ counts }: { counts: Record<TestExecutionStatus, number> }) {
  const keys = [...CORE_STATUSES, ...(['STOPPED', 'NOT_RUN'] as const).filter((s) => counts[s] > 0)];
  const data = keys.map((s) => ({ key: s, label: s, value: counts[s], color: STATUS_COLORS[s] }));
  return <ChartFrame title="Test durumu dağılımı" data={data} emptyText="Henüz test sonucu yok." slantedTicks />;
}

const SEVERITY_ORDER: readonly Severity[] = ['HIGH', 'MEDIUM', 'LOW', 'UNKNOWN'];
const SEVERITY_COLORS: Record<Severity, string> = {
  HIGH: 'var(--error)',
  MEDIUM: 'var(--fail)',
  LOW: 'var(--process)',
  UNKNOWN: 'var(--muted)',
};

/** Güvenlik bulgularının önem derecesi dağılımı (doğrulama sınıfından bağımsız). */
export function SeverityChart({ findings }: { findings: readonly SecurityFinding[] }) {
  const data = SEVERITY_ORDER.map((s) => ({
    key: s,
    label: SEVERITY_LABEL[s],
    value: findings.filter((f) => f.severity === s).length,
    color: SEVERITY_COLORS[s],
  }));
  return (
    <ChartFrame
      title="Önem derecesi dağılımı"
      data={data}
      emptyText="Bu analizde güvenlik bulgusu yok."
      footnote="Önem derecesi, bulgunun doğrulanıp doğrulanmadığını göstermez."
    />
  );
}

/** Precision / Recall / F1 (0–1 sabit eksen). Ölçülemeyen metrik çubuk olarak çizilmez. */
export function MetricsChart({ summary }: { summary: EvaluationSummary }) {
  const all = [
    { key: 'precision', label: 'Precision', value: summary.precision },
    { key: 'recall', label: 'Recall', value: summary.recall },
    { key: 'f1', label: 'F1', value: summary.f1 },
  ];
  const measurable = all.filter((m): m is { key: string; label: string; value: number } => m.value !== null);
  const missing = all.filter((m) => m.value === null).map((m) => m.label);
  return (
    <ChartFrame
      title="Güvenlik tespit metrikleri"
      data={measurable.map((m) => ({ ...m, color: 'var(--accent)' }))}
      emptyText="Metrikler ölçülemedi (payda sıfır)."
      format={(v) => formatMetric(v)}
      domain={[0, 1]}
      footnote={missing.length > 0 ? `Ölçülemedi: ${missing.join(', ')}` : undefined}
    />
  );
}
