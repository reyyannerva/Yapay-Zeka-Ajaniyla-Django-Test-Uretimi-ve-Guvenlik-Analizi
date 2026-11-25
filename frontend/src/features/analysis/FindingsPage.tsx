import { useMemo, useState } from 'react';

import { Card } from '../../components/ui/Card';
import { CodeBlock } from '../../components/ui/CodeBlock';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { HttpMethodBadge } from '../../components/ui/HttpMethodBadge';
import { Spinner } from '../../components/ui/Spinner';
import { Badge } from '../../components/ui/StatusBadge';
import { FINDING_SOURCE_LABEL } from '../../lib/analysis-labels';
import { FINDING_META, SEVERITY_LABEL, findingTone } from '../../lib/analysis-status';
import { getRecommendation } from '../../lib/recommendations';
import type { AnalysisRunStatus, SecurityFinding, SecurityFindingClassification, Severity } from '../../types';
import { SeverityChart } from './charts';
import {
  useAnalysisContext,
  useEndpoints,
  useGeneratedTests,
  useSecurityFindings,
  useTestResults,
} from './useAnalysisData';

const CLASS_ORDER: readonly SecurityFindingClassification[] = ['VERIFIED', 'POSSIBLE', 'UNCERTAIN'];
const SEVERITY_ORDER: readonly Severity[] = ['HIGH', 'MEDIUM', 'LOW', 'UNKNOWN'];
const SCAN_PENDING: readonly AnalysisRunStatus[] = ['QUEUED', 'ANALYZING', 'GENERATING', 'VALIDATING', 'EXECUTING', 'SCANNING'];

const SEVERITY_SQUARE: Record<Severity, string> = {
  HIGH: 'bg-error',
  MEDIUM: 'bg-fail',
  LOW: 'bg-process',
  UNKNOWN: 'bg-border-strong',
};

/** Önem derecesi: doğrulama sınıfından ayrı bir işaret (kare + metin). */
export function SeverityMark({ severity }: { severity: Severity }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-fg" data-severity={severity}>
      <span aria-hidden="true" className={`h-2.5 w-2.5 rounded-sm ${SEVERITY_SQUARE[severity]}`} />
      {`Önem: ${SEVERITY_LABEL[severity]}`}
    </span>
  );
}

/** Doğrulama sınıfı: VERIFIED asla başarı (yeşil) tonu almaz. */
export function ClassificationBadge({ finding }: { finding: SecurityFinding }) {
  return (
    <Badge tone={findingTone(finding.classification, finding.severity)}>{FINDING_META[finding.classification].label}</Badge>
  );
}

const CLASS_EXPLAIN: Record<SecurityFindingClassification, string> = {
  VERIFIED: 'Çalışan sistemde kanıtlandı.',
  POSSIBLE: 'Yalnızca statik/kısmi kanıt var; çalışan sistemde doğrulanmadı.',
  UNCERTAIN: 'Kanıt yetersiz; sonuç belirsiz. Elle inceleme gerekir.',
};

function Fact({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex min-w-0 flex-col gap-0.5">
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="break-words text-sm text-fg">{children}</dd>
    </div>
  );
}

export function FindingsPage() {
  const { run } = useAnalysisContext();
  const findings = useSecurityFindings(run.id);
  const endpoints = useEndpoints(run.id);
  const tests = useGeneratedTests(run.id);
  const results = useTestResults(run.id);
  const [cls, setCls] = useState<'ALL' | SecurityFindingClassification>('ALL');
  const [sev, setSev] = useState<'ALL' | Severity>('ALL');
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const rows = findings.data ?? [];
  const visible = useMemo(
    () => rows.filter((f) => (cls === 'ALL' || f.classification === cls) && (sev === 'ALL' || f.severity === sev)),
    [rows, cls, sev],
  );

  if (findings.isLoading) return <Spinner label="Bulgular yükleniyor" />;
  if (findings.isError) return <ErrorState title="Güvenlik bulguları alınamadı" description="Lütfen sayfayı yenileyip tekrar deneyin." />;
  if (rows.length === 0) {
    return SCAN_PENDING.includes(run.status) ? (
      <EmptyState title="Güvenlik taraması henüz tamamlanmadı" description="Bulgular tarama aşamasından sonra listelenir." />
    ) : (
      <EmptyState
        title="Güvenlik bulgusu bulunmadı"
        description="Bu analizde kayıtlı bulgu yok. Bu, uygulamanın güvenli olduğu anlamına gelmez; yalnızca kapsamdaki kontrollerde bulgu çıkmadığını gösterir."
      />
    );
  }

  const selected = visible.find((f) => f.id === selectedId) ?? visible[0];
  const endpoint = selected ? endpoints.data?.find((e) => e.id === selected.endpoint) : undefined;
  const execution = selected ? results.data?.find((r) => r.id === selected.test_execution) : undefined;
  const relatedTest = execution ? tests.data?.find((t) => t.id === execution.generated_test) : undefined;
  const recommendation = selected ? getRecommendation(selected.recommendation_key) : null;

  return (
    <section aria-label="Güvenlik bulguları" className="flex flex-col gap-4">
      {SCAN_PENDING.includes(run.status) || run.status === 'FAILED' ? (
        <p role="note" className="rounded-md border border-fail bg-fail-bg px-3 py-2 text-sm text-fg">
          Kısmi sonuç: analiz tamamlanmadığı için bulgu listesi eksik olabilir.
        </p>
      ) : null}
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <Card className="flex flex-col gap-3">
          <h2 className="font-display text-lg font-semibold text-fg">Doğrulama sınıfları</h2>
          <ul className="flex flex-col gap-2 text-sm">
            {CLASS_ORDER.map((c) => (
              <li key={c} className="flex items-center justify-between gap-3">
                <span className="flex items-center gap-2">
                  <Badge tone={FINDING_META[c].tone}>{FINDING_META[c].label}</Badge>
                  <span className="text-xs text-muted">{CLASS_EXPLAIN[c]}</span>
                </span>
                <span className="font-mono font-semibold text-fg">{rows.filter((f) => f.classification === c).length}</span>
              </li>
            ))}
          </ul>
        </Card>
        <SeverityChart findings={rows} />
      </div>

      <div className="flex flex-wrap gap-3">
        <label className="flex flex-col gap-1 text-xs font-medium text-muted">
          Doğrulama sınıfı
          <select
            value={cls}
            onChange={(e) => setCls(e.target.value as typeof cls)}
            className="rounded-md border border-border-strong bg-surface px-3 py-2 text-sm text-fg focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
          >
            <option value="ALL">Tümü</option>
            {CLASS_ORDER.map((c) => (
              <option key={c} value={c}>{FINDING_META[c].label}</option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs font-medium text-muted">
          Önem derecesi
          <select
            value={sev}
            onChange={(e) => setSev(e.target.value as typeof sev)}
            className="rounded-md border border-border-strong bg-surface px-3 py-2 text-sm text-fg focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
          >
            <option value="ALL">Tümü</option>
            {SEVERITY_ORDER.map((s) => (
              <option key={s} value={s}>{SEVERITY_LABEL[s]}</option>
            ))}
          </select>
        </label>
      </div>

      {visible.length === 0 ? (
        <EmptyState title="Filtrelerle eşleşen bulgu yok" description="Filtreleri değiştirin." />
      ) : (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
          <ul className="flex min-w-0 flex-col gap-1 self-start rounded-lg border border-border bg-surface p-2" aria-label="Bulgu listesi">
            {visible.map((f) => {
              const active = selected?.id === f.id;
              return (
                <li key={f.id}>
                  <button
                    type="button"
                    aria-current={active ? 'true' : undefined}
                    onClick={() => setSelectedId(f.id)}
                    className={`flex w-full flex-col gap-1.5 rounded-md px-3 py-2 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent ${
                      active ? 'bg-accent-soft' : 'hover:bg-surface-2'
                    }`}
                  >
                    <span className="text-sm font-medium text-fg">{f.title}</span>
                    <span className="flex flex-wrap items-center gap-2">
                      <ClassificationBadge finding={f} />
                      <SeverityMark severity={f.severity} />
                      <span className="text-xs text-muted">{FINDING_SOURCE_LABEL[f.source]}</span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>

          {selected ? (
            <Card className="flex min-w-0 flex-col gap-4" role="region" aria-label="Bulgu ayrıntısı">
              <div className="flex flex-col gap-2">
                <h2 className="font-display text-lg font-semibold text-fg">{selected.title}</h2>
                <div className="flex flex-wrap items-center gap-3">
                  <ClassificationBadge finding={selected} />
                  <SeverityMark severity={selected.severity} />
                </div>
                <p className="text-sm text-muted">{CLASS_EXPLAIN[selected.classification]}</p>
                {selected.description ? <p className="text-sm text-fg">{selected.description}</p> : null}
              </div>
              <dl className="grid gap-3 sm:grid-cols-2">
                <Fact label="Kaynak / kural">
                  {FINDING_SOURCE_LABEL[selected.source]} · <code className="font-mono text-xs">{selected.rule_id}</code>
                </Fact>
                <Fact label="Dosya ve konum">
                  {selected.file_path ? (
                    <code className="break-all font-mono text-xs">{`${selected.file_path}${selected.line_number !== null ? `:${selected.line_number}` : ''}`}</code>
                  ) : (
                    <span className="text-muted">Konum bilgisi yok</span>
                  )}
                </Fact>
                <Fact label="Endpoint">
                  {endpoint ? (
                    <span className="inline-flex flex-wrap items-center gap-2">
                      <HttpMethodBadge method={endpoint.http_method} />
                      <code className="break-all font-mono text-xs">{endpoint.path}</code>
                    </span>
                  ) : (
                    <span className="text-muted">Endpoint ile ilişkili değil</span>
                  )}
                </Fact>
                <Fact label="İlgili test">
                  {relatedTest ? <code className="break-all font-mono text-xs">{relatedTest.test_name}</code> : <span className="text-muted">Test kaydı yok</span>}
                </Fact>
              </dl>
              <div className="flex flex-col gap-2">
                <h3 className="text-sm font-semibold text-fg">Kanıt</h3>
                {selected.evidence_excerpt ? (
                  <CodeBlock code={selected.evidence_excerpt} label={`${selected.title} kanıtı`} maxHeightClass="max-h-48" />
                ) : (
                  <p className="text-sm text-muted">Bu bulgu için kanıt kaydı bulunmuyor.</p>
                )}
              </div>
              <div className="flex flex-col gap-1">
                <h3 className="text-sm font-semibold text-fg">Düzeltme önerisi</h3>
                {recommendation ? (
                  <>
                    <p className="text-sm font-medium text-fg">{recommendation.title}</p>
                    <p className="text-sm text-fg">{recommendation.text}</p>
                    <p className="text-xs text-muted">{`Referans: ${recommendation.reference}`}</p>
                  </>
                ) : (
                  <p className="text-sm text-muted">Bu bulgu türü için kayıtlı bir düzeltme önerisi yok.</p>
                )}
              </div>
            </Card>
          ) : null}
        </div>
      )}
    </section>
  );
}
