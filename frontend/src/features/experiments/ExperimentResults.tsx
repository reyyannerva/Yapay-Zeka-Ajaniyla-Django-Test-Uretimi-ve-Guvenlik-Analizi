import { Badge } from '../../components/ui/StatusBadge';
import { Card } from '../../components/ui/Card';
import { DataTable } from '../../components/ui/DataTable';
import type { DataTableColumn } from '../../components/ui/DataTable';
import { EmptyState } from '../../components/ui/EmptyState';
import { LAYER_TITLES, experiment, formatRatio, targetTone } from './experimentData';
import type { ExactMetric, LayerResult, MethodResult } from './experimentData';

const COLUMNS: readonly DataTableColumn<MethodResult>[] = [
  { key: 'method', header: 'Yöntem', cell: (m) => <span className="font-medium">{m.label}</span> },
  { key: 'syntax', header: 'Sözdizimi geçerli', cell: (m) => `${m.syntaxValid.count}/${m.syntaxValid.of}` },
  { key: 'collected', header: 'Toplanan', cell: (m) => `${m.collected.count}/${m.collected.of}` },
  {
    key: 'fpe',
    header: 'İlk geçişte çalıştırılabilir (pay/payda)',
    cell: (m) => `${m.firstPassExecutable.count}/${m.firstPassExecutable.of} · ${formatRatio(m.firstPassExecutable)}`,
  },
  {
    key: 's5',
    header: 'PASS / FAIL / ERROR / TIMEOUT / NOT_RUN',
    cell: (m) => `${m.status5.PASS} / ${m.status5.FAIL} / ${m.status5.ERROR} / ${m.status5.TIMEOUT} / ${m.status5.NOT_RUN}`,
  },
  {
    key: 'cm',
    header: 'TP / FP / TN / FN',
    cell: (m) => `${m.confusion.TP} / ${m.confusion.FP} / ${m.confusion.TN} / ${m.confusion.FN}`,
  },
  { key: 'p', header: 'Precision', cell: (m) => formatRatio(m.precision) },
  { key: 'r', header: 'Recall', cell: (m) => formatRatio(m.recall) },
  { key: 'f1', header: 'F1', cell: (m) => formatRatio(m.f1) },
  { key: 'tf1', header: 'F1 ≥ 0,80', cell: (m) => <Badge tone={targetTone(m.targets.f1)}>{m.targets.f1}</Badge> },
  {
    key: 'tex',
    header: 'Çalıştırılabilirlik ≥ %70',
    cell: (m) => <Badge tone={targetTone(m.targets.executability)}>{m.targets.executability}</Badge>,
  },
];

/** Yatay oran çubuğu. Ölçülemeyen değer için çubuk ÇİZİLMEZ (0 gibi görünmesin), yalnızca metin yazılır. */
function RatioBar({ label, metric }: { label: string; metric: ExactMetric }) {
  const pct = metric.value === null ? null : Math.round(metric.value * 100);
  return (
    <div className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1 text-sm">
      <span className="w-28 shrink-0 text-muted sm:w-40">{label}</span>
      {pct === null ? (
        <span className="italic text-muted" data-testid="not-measurable">
          {metric.display}
        </span>
      ) : (
        <span className="flex min-w-0 flex-1 items-center gap-2">
          <span
            className="h-2.5 rounded-full bg-accent"
            style={{ width: `${pct}%`, minWidth: '2px' }}
            role="img"
            aria-label={`${label}: ${formatRatio(metric)}`}
          />
          <span className="tabular-nums">{formatRatio(metric)}</span>
        </span>
      )}
    </div>
  );
}

function LayerSection({ layer }: { layer: LayerResult }) {
  const methods = Object.entries(layer.httpMethods)
    .map(([m, n]) => `${m} ${n}`)
    .join(' · ');
  return (
    <section aria-labelledby={`layer-${layer.key}`} className="flex min-w-0 flex-col gap-4">
      <h2 id={`layer-${layer.key}`} className="font-display text-lg font-semibold">
        {LAYER_TITLES[layer.key]}
      </h2>
      <p className="text-sm text-muted">
        {layer.scenarios} senaryo · HTTP metotları: {methods} · bilinen kusur: {layer.positives} · LLM kaynağı:{' '}
        {layer.llmStatus === 'ARCHIVED_FIRST_PASS' ? 'H3-05 arşiv ilk geçiş çıktısı' : 'H5-05 yeni Groq koşusu'} (
        {layer.llmModel ?? '—'}) · karşılaştırılabilir: {layer.comparable ? 'evet' : `hayır (${layer.comparabilityReason})`}
      </p>
      <DataTable
        columns={COLUMNS}
        rows={layer.methods}
        rowKey={(m) => m.key}
        emptyState={<EmptyState title="Sonuç yok" description="Bu katman için deney sonucu bulunmuyor." />}
      />
      <div className="grid min-w-0 gap-4 lg:grid-cols-2">
        <Card>
          <h3 className="mb-3 text-sm font-semibold">İlk geçişte çalıştırılabilirlik</h3>
          <div className="flex flex-col gap-2">
            {layer.methods.map((m) => (
              <RatioBar key={m.key} label={m.label} metric={m.firstPassExecutable} />
            ))}
          </div>
        </Card>
        <Card>
          <h3 className="mb-3 text-sm font-semibold">F1 (güvenlik tespiti)</h3>
          <div className="flex flex-col gap-2">
            {layer.methods.map((m) => (
              <RatioBar key={m.key} label={m.label} metric={m.f1} />
            ))}
          </div>
          {layer.positives === 0 ? (
            <p className="mt-3 text-xs text-muted">
              Bu katmanda bilinen kusur yok (TP+FN = 0); F1 tanım gereği ölçülemez ve 0 olarak gösterilmez.
            </p>
          ) : null}
        </Card>
      </div>
      <p className="text-xs text-muted">
        Hibrit kararları: {layer.hybrid.rule_based_candidates} kural tabanlı + {layer.hybrid.llm_candidates} LLM aday ·
        anlamsal anahtarı eşit {layer.hybrid.semantic_key_equal_pairs} çift (kodu birebir aynı:{' '}
        {layer.hybrid.code_identical_pairs}) · yinelenen {layer.hybrid.duplicates} · birleştirilen{' '}
        {layer.hybrid.merged} · çözülen/çözülmeyen çelişki {layer.hybrid.conflicts_resolved}/
        {layer.hybrid.conflicts_unresolved} · nihai test modülü {layer.hybrid.final_tests}
      </p>
    </section>
  );
}

export function ExperimentResults() {
  return (
    <div className="flex min-w-0 flex-col gap-6">
      <header className="flex flex-col gap-2">
        <h1 className="font-display text-2xl font-semibold">Deney sonuçları</h1>
        <p className="flex flex-wrap items-center gap-2 text-sm text-muted">
          <Badge tone="process">ÇEVRİMDIŞI DENEY</Badge>
          <span>
            H5-05 ({experiment.issue}) geliştirme kümesi sonuçları. Canlı bir analiz kaydı veya DEMO verisi değildir;
            bağımsız test kümesinde doğrulanmış nihai performans olarak yorumlanmamalıdır.
          </span>
        </p>
      </header>

      <Card className="flex min-w-0 flex-col gap-1 break-words text-sm">
        <span>
          Model: <strong>{experiment.model}</strong> · istem {experiment.promptVersion} · sıcaklık 0,0 (planlanan:{' '}
          {experiment.plannedModel})
        </span>
        <span className="text-muted">
          Kaynak: <code className="break-all">{experiment.source}</code> · SHA-256 {experiment.sourceSha256.slice(0, 12)}… · koşu{' '}
          {experiment.runTimestampUtc}
        </span>
        <span className="text-muted">
          Hedefler: F1 ≥ 0,80 ve ilk geçişte çalıştırılabilirlik ≥ %70. İlk geçiş: PASS veya FAIL sonuçlanan senaryo
          / tüm senaryolar (otomatik düzeltme yok).
        </span>
      </Card>

      {experiment.layers.map((layer) => (
        <LayerSection key={layer.key} layer={layer} />
      ))}

      <Card className="text-sm">
        <h2 className="mb-2 font-semibold">Yorum ve sınırlılıklar</h2>
        <ul className="list-disc space-y-1 pl-5 text-muted">
          <li>Üç yöntem iki katmanda da aynı karışıklık matrisini verdi; hibritin metrik üstünlüğü gösterilmedi.</li>
          <li>Hibritin katkısı doğrulama kapsamıdır: bir senaryoda kural tabanlı rota kontrolü ile LLM gövde kontrolü birleştirildi.</li>
          <li>Katman B F1 = 1,00 yalnızca 3 kusurlu, ekip içi hazırlanmış kontrollü kümeye aittir; genellenebilir değildir.</li>
        </ul>
      </Card>
    </div>
  );
}
