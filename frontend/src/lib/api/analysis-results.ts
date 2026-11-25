// Analiz sonuç servisi (#40). Ekranlar yalnızca bu dosyadaki fonksiyonları çağırır.
// Şimdilik tüm fonksiyonlar `mock/analysis-results.ts` DEMO fixture'larını döndürür; gerçek API
// entegrasyonunda (#41) yalnızca bu fonksiyonların gövdeleri `apiFetch` çağrılarıyla değişir,
// imzalar ve dönüş tipleri aynı kalır.
import type {
  ApiError,
  EndpointAnalysis,
  EvaluationCounts,
  ExecutionSnapshot,
  GeneratedTest,
  ReportFormat,
  ReportRecord,
  ReportSection,
  SecurityFinding,
  TestExecutionResult,
} from '../../types';
import { reportScopeFor } from '../report-sections';
import { advanceRun2, isRun2Finished, mockRunResults } from './mock/analysis-results';
import type { RunResults } from './mock/analysis-results';
import { mockAnalysisRuns } from './mock';

function notFound(): ApiError {
  return { status: 404, body: { detail: 'No AnalysisRun matches the given query.' } };
}

function runResults(runId: number): Promise<RunResults> {
  const data = mockRunResults[runId];
  return data ? Promise.resolve(data) : Promise.reject(notFound());
}

export function listEndpoints(runId: number): Promise<EndpointAnalysis[]> {
  return runResults(runId).then((d) => d.endpoints.map((e) => ({ ...e })));
}

export function listGeneratedTests(runId: number): Promise<GeneratedTest[]> {
  return runResults(runId).then((d) => d.tests.map((t) => ({ ...t })));
}

export function listTestResults(runId: number): Promise<TestExecutionResult[]> {
  return runResults(runId).then((d) => d.results());
}

export function listSecurityFindings(runId: number): Promise<SecurityFinding[]> {
  return runResults(runId).then((d) => d.findings.map((f) => ({ ...f })));
}

/** Altın etiketli referansla karşılaştırma sayımları; veri yoksa null (metrik üretilmez). */
export function getEvaluation(runId: number): Promise<EvaluationCounts | null> {
  return runResults(runId).then((d) => (d.evaluation ? { ...d.evaluation } : null));
}

export interface ExecutionStreamOptions {
  /** Mock akışta iki adım arası süre (ms). */
  intervalMs?: number;
}

/**
 * Test yürütme akışına abone olur. Dönen fonksiyon aboneliği kapatır (zamanlayıcıyı temizler).
 * Mock: #2 (EXECUTING) için deterministik bir adım dizisi oynatılır; diğer analizler tek bir son
 * anlık görüntü gönderir. Gerçek entegrasyonda yoklama veya sunucu olaylarıyla değiştirilecektir.
 */
export function subscribeExecution(
  runId: number,
  onSnapshot: (snapshot: ExecutionSnapshot) => void,
  onError: (error: ApiError) => void,
  options: ExecutionStreamOptions = {},
): () => void {
  const data = mockRunResults[runId];
  const run = mockAnalysisRuns.find((r) => r.id === runId);
  let closed = false;
  if (!data || !run) {
    queueMicrotask(() => {
      if (!closed) onError(notFound());
    });
    return () => {
      closed = true;
    };
  }

  let current = data.results();
  const live = run.status === 'EXECUTING' && !isRun2Finished(current);
  queueMicrotask(() => {
    if (!closed) onSnapshot({ results: current, finished: !live });
  });
  if (!live) {
    return () => {
      closed = true;
    };
  }

  const timer = setInterval(() => {
    current = advanceRun2(current);
    const finished = isRun2Finished(current);
    onSnapshot({ results: current, finished });
    if (finished) clearInterval(timer);
  }, options.intervalMs ?? 1500);

  return () => {
    closed = true;
    clearInterval(timer);
  };
}

export interface PrepareReportInput {
  format: ReportFormat;
  sections: ReportSection[];
}

/** Rapor hazırlama isteği. Mock: kısa bir gecikmeyle kayıt döner; hata senaryosunda reddeder. */
export function prepareReport(
  runId: number,
  input: PrepareReportInput,
  delayMs = 700,
): Promise<ReportRecord> {
  const data = mockRunResults[runId];
  const run = mockAnalysisRuns.find((r) => r.id === runId);
  if (!data || !run) return Promise.reject(notFound());
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (data.reportFails) {
        reject({ status: 500, body: { detail: 'Rapor hazırlanamadı (DEMO hata senaryosu).' } } satisfies ApiError);
        return;
      }
      resolve({
        id: runId * 100 + (input.format === 'PDF' ? 1 : 2),
        analysis_run: runId,
        format: input.format,
        scope: reportScopeFor(run.status),
        sections: [...input.sections],
        file_size_bytes: 0,
        created_at: new Date().toISOString(),
      });
    }, delayMs);
  });
}

/**
 * DEMO JSON rapor içeriği: yalnızca seçilen bölümleri içerir ve açıkça DEMO olarak işaretlenir.
 * PDF içeriği frontend'de üretilmez (backend rapor servisi kapsamındadır).
 */
export function buildDemoJsonReport(runId: number, sections: readonly ReportSection[]): Record<string, unknown> {
  const data = mockRunResults[runId];
  const run = mockAnalysisRuns.find((r) => r.id === runId);
  if (!data || !run) throw notFound();
  const doc: Record<string, unknown> = {
    demo: true,
    note: 'ÖRNEK VERİ — gerçek bir analiz sonucu değildir.',
    analysis_run: run.id,
    scope: reportScopeFor(run.status),
    sections: [...sections],
  };
  if (sections.includes('ANALYSIS_SUMMARY')) {
    doc.analysis_summary = {
      project: run.project,
      status: run.status,
      method: run.method,
      llm_provider: run.llm_provider,
      fallback_enabled: run.fallback_enabled,
      endpoint_count: data.endpoints.length,
    };
  }
  if (sections.includes('GENERATED_TESTS')) {
    doc.generated_tests = data.tests.map((t) => ({
      id: t.id,
      test_name: t.test_name,
      generation_method: t.generation_method,
      validation_status: t.validation_status,
    }));
  }
  if (sections.includes('EXECUTION_RESULTS')) {
    doc.execution_results = data.results().map((r) => ({
      generated_test: r.generated_test,
      status: r.status,
      duration_ms: r.duration_ms,
    }));
  }
  if (sections.includes('SECURITY_FINDINGS')) {
    doc.security_findings = data.findings.map((f) => ({
      id: f.id,
      title: f.title,
      severity: f.severity,
      classification: f.classification,
    }));
  }
  if (sections.includes('EVALUATION_METRICS')) {
    doc.evaluation = data.evaluation;
  }
  return doc;
}
