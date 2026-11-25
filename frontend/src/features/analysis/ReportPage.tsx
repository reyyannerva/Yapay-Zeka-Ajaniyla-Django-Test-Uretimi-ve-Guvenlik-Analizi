import { useEffect, useRef, useState } from 'react';

import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { Spinner } from '../../components/ui/Spinner';
import { buildDemoJsonReport, prepareReport } from '../../lib/api/analysis-results';
import { isApiError } from '../../lib/api/client';
import {
  REPORT_SECTIONS,
  canPrepareReport,
  reportFileName,
  toggleSection,
  validateSelection,
} from '../../lib/report-sections';
import type { ReportFormat, ReportRecord, ReportSection, ReportStatus } from '../../types';
import { EvaluationPanel } from './EvaluationPanel';
import { useAnalysisContext, useEndpoints, useEvaluation, useGeneratedTests, useSecurityFindings } from './useAnalysisData';
import { demoOnly } from './demoOnly';

const DEFAULT_SECTIONS: ReportSection[] = ['ANALYSIS_SUMMARY', 'EXECUTION_RESULTS', 'SECURITY_FINDINGS'];

/** Tarayıcıda JSON dosyası indirir; geçici blob URL hemen serbest bırakılır. */
function downloadJson(content: unknown, fileName: string) {
  const blob = new Blob([JSON.stringify(content, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  try {
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    a.rel = 'noopener';
    document.body.appendChild(a);
    a.click();
    a.remove();
  } finally {
    URL.revokeObjectURL(url);
  }
}

function ReportPageDemo({ delayMs }: { delayMs?: number }) {
  const { run } = useAnalysisContext();
  const evaluation = useEvaluation(run.id);
  const endpoints = useEndpoints(run.id);
  const tests = useGeneratedTests(run.id);
  const findings = useSecurityFindings(run.id);
  const [sections, setSections] = useState<ReportSection[]>(DEFAULT_SECTIONS);
  const [format, setFormat] = useState<ReportFormat>('PDF');
  const [status, setStatus] = useState<ReportStatus>('idle');
  const [record, setRecord] = useState<ReportRecord | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [downloaded, setDownloaded] = useState(false);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  if (evaluation.isLoading || endpoints.isLoading || tests.isLoading || findings.isLoading) {
    return <Spinner label="Rapor bilgileri yükleniyor" />;
  }
  if (evaluation.isError || endpoints.isError || tests.isError || findings.isError) {
    return <ErrorState title="Rapor bilgileri alınamadı" description="Lütfen sayfayı yenileyip tekrar deneyin." />;
  }
  if (!canPrepareReport(run.status)) {
    return (
      <div className="flex flex-col gap-4">
        <EmptyState title="Rapor henüz hazırlanamaz" description="Rapor, analiz tamamlandığında veya sonuçlandığında (kısmi sonuçla) hazırlanabilir." />
        <EvaluationPanel evaluation={evaluation.data ?? null} />
      </div>
    );
  }
  const hasData = (endpoints.data?.length ?? 0) + (tests.data?.length ?? 0) + (findings.data?.length ?? 0) > 0;
  if (!hasData) {
    return <EmptyState title="Rapora konacak veri bulunmuyor" description="Bu analiz sonuç üretmeden sona erdi; rapor oluşturulamaz." />;
  }

  const hasEvaluation = evaluation.data !== null && evaluation.data !== undefined;
  const selectionError = validateSelection(sections, { hasEvaluation });
  const partial = run.status !== 'COMPLETED';

  async function onPrepare() {
    setMessage(null);
    if (selectionError) {
      setMessage(selectionError);
      return;
    }
    setStatus('preparing');
    setRecord(null);
    setDownloaded(false);
    try {
      const rec = await prepareReport(run.id, { format, sections }, delayMs);
      if (!mounted.current) return;
      setRecord(rec);
      setStatus('ready');
    } catch (err) {
      if (!mounted.current) return;
      setStatus('error');
      const detail = isApiError(err) && 'detail' in err.body ? String(err.body.detail) : 'Beklenmeyen bir hata oluştu.';
      setMessage(detail);
    }
  }

  return (
    <section aria-label="Raporlama" className="flex flex-col gap-4">
      {partial ? (
        <p role="note" className="rounded-md border border-fail bg-fail-bg p-3 text-sm text-fg">
          Analiz tamamlanmadığı için rapor kısmi (PARTIAL) olarak hazırlanır.
        </p>
      ) : null}
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
        <Card className="flex flex-col gap-4">
          <fieldset className="flex flex-col gap-2">
            <legend className="mb-1 font-display text-lg font-semibold text-fg">Rapor bölümleri</legend>
            {REPORT_SECTIONS.map((s) => {
              const disabled = s.key === 'EVALUATION_METRICS' && !hasEvaluation;
              const id = `section-${s.key}`;
              return (
                <div key={s.key} className={`flex items-start gap-3 rounded-md border border-border p-3 ${disabled ? 'opacity-60' : ''}`}>
                  <input
                    id={id}
                    type="checkbox"
                    checked={sections.includes(s.key)}
                    disabled={disabled}
                    onChange={() => {
                      setSections((cur) => toggleSection(cur, s.key));
                      setStatus('idle');
                      setMessage(null);
                    }}
                    className="mt-0.5 h-4 w-4 accent-[var(--accent)]"
                    aria-describedby={`${id}-desc`}
                  />
                  <label htmlFor={id} className="flex flex-col">
                    <span className="text-sm font-medium text-fg">{s.label}</span>
                    <span id={`${id}-desc`} className="text-xs text-muted">
                      {disabled ? 'Değerlendirme verisi olmadığı için eklenemez.' : s.description}
                    </span>
                  </label>
                </div>
              );
            })}
          </fieldset>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="ghost"
              onClick={() => {
                setSections(REPORT_SECTIONS.map((s) => s.key).filter((k) => k !== 'EVALUATION_METRICS' || hasEvaluation));
                setStatus('idle');
              }}
            >
              Tümünü seç
            </Button>
            <Button
              variant="ghost"
              onClick={() => {
                setSections([]);
                setStatus('idle');
              }}
            >
              Seçimi temizle
            </Button>
          </div>
          <fieldset className="flex flex-col gap-2">
            <legend className="mb-1 text-sm font-semibold text-fg">Biçim</legend>
            <div className="flex gap-4">
              {(['PDF', 'JSON'] as const).map((f) => (
                <label key={f} className="inline-flex items-center gap-2 text-sm text-fg">
                  <input
                    type="radio"
                    name="report-format"
                    value={f}
                    checked={format === f}
                    onChange={() => {
                      setFormat(f);
                      setStatus('idle');
                    }}
                    className="h-4 w-4 accent-[var(--accent)]"
                  />
                  {f}
                </label>
              ))}
            </div>
          </fieldset>
        </Card>

        <Card className="flex flex-col gap-4" aria-live="polite">
          <h2 className="font-display text-lg font-semibold text-fg">Seçili bölümler</h2>
          {sections.length === 0 ? (
            <p className="text-sm text-muted">Bölüm seçilmedi.</p>
          ) : (
            <ol className="list-decimal pl-5 text-sm text-fg" data-testid="selected-sections">
              {REPORT_SECTIONS.filter((s) => sections.includes(s.key)).map((s) => (
                <li key={s.key}>{s.label}</li>
              ))}
            </ol>
          )}
          {message ? (
            <p role="alert" className="rounded-md border border-error bg-error-bg p-3 text-sm">
              {message}
            </p>
          ) : null}
          <Button onClick={onPrepare} disabled={status === 'preparing'} aria-busy={status === 'preparing'}>
            {status === 'preparing' ? 'Rapor hazırlanıyor…' : `${format} raporu hazırla`}
          </Button>
          {status === 'preparing' ? <Spinner label="Rapor hazırlanıyor" /> : null}
          {status === 'error' ? (
            <p className="text-sm text-muted">Rapor hazırlanamadı. Seçimi değiştirmeden tekrar deneyebilirsiniz.</p>
          ) : null}
          {status === 'ready' && record ? (
            <div className="flex flex-col gap-2 rounded-md border border-pass bg-pass-bg p-3" data-testid="report-ready">
              <p className="text-sm font-medium text-fg">
                {`${record.format} rapor kaydı hazır (${record.scope === 'FULL' ? 'tam' : 'kısmi'} · ${record.sections.length} bölüm) — DEMO.`}
              </p>
              {record.format === 'JSON' ? (
                <Button
                  variant="ghost"
                  onClick={() => {
                    downloadJson(buildDemoJsonReport(run.id, record.sections), reportFileName(run.id, 'JSON'));
                    setDownloaded(true);
                  }}
                >
                  JSON indir (DEMO)
                </Button>
              ) : (
                <>
                  <Button variant="ghost" disabled aria-describedby="pdf-download-note">
                    PDF indir
                  </Button>
                  <p id="pdf-download-note" className="text-xs text-muted">
                    PDF dosyası backend rapor servisiyle üretilecektir (#41 sonrası). Bu DEMO'da PDF dosyası oluşturulmaz; JSON biçimiyle örnek içerik indirilebilir.
                  </p>
                </>
              )}
              {downloaded ? (
                <p role="status" className="text-sm font-medium text-pass">
                  {`İndirme başarılı: ${reportFileName(run.id, 'JSON')}`}
                </p>
              ) : null}
            </div>
          ) : null}
        </Card>
      </div>
      <EvaluationPanel evaluation={evaluation.data ?? null} />
    </section>
  );
}

/** DEMO kaynağında H5-02 ekranı; gerçek analizde "servis bağlı değil" durumu (H5-03 / #41). */
export const ReportPage = demoOnly(ReportPageDemo, 'Rapor üretimi');
