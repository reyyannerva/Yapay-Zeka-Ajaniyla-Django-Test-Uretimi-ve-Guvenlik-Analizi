import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { useOutletContext, useParams } from 'react-router-dom';

import {
  getEvaluation,
  listEndpoints,
  listGeneratedTests,
  listSecurityFindings,
  listTestResults,
  subscribeExecution,
} from '../../lib/api/analysis-results';
import { getAnalysisRun } from '../../lib/api/analysis-runs';
import { getDemoAnalysisRun } from '../../lib/api/demo-analysis';
import { queryKeys } from '../../lib/queryKeys';
import type { AnalysisRunDetail, ApiError, ExecutionSnapshot } from '../../types';

/** URL'deki :id değerini doğrular; geçersizse null. */
export function useRunId(): number | null {
  const { id } = useParams();
  const parsed = Number(id);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

/**
 * Veri kaynağı: `api` gerçek Django/DRF kaydı (H5-03 / #41), `demo` H5-02 prototip verisi.
 * İkisi ayrı rotalarda (/analyses, /demo/analyses) ve ayrı önbellek anahtarlarında tutulur.
 */
export type AnalysisSource = 'api' | 'demo';

/** Gerçek analiz bitmemişse durumu bu aralıkla yeniden sorgulanır; uç durumda yoklama durur. */
export const RUN_POLL_INTERVAL_MS = 15_000;
const TERMINAL_RUN_STATUSES = ['COMPLETED', 'FAILED', 'CANCELLED'];

export function useAnalysisRun(runId: number | null, source: AnalysisSource = 'api') {
  return useQuery({
    queryKey: source === 'api' ? queryKeys.analysisRuns.detail(runId ?? 0) : queryKeys.demo.analysisRuns.detail(runId ?? 0),
    queryFn: ({ signal }) => (source === 'api' ? getAnalysisRun(runId as number, signal) : getDemoAnalysisRun(runId as number)),
    enabled: runId !== null,
    refetchInterval: (query) => {
      if (source !== 'api') return false;
      const status = query.state.data?.status;
      return status && !TERMINAL_RUN_STATUSES.includes(status) ? RUN_POLL_INTERVAL_MS : false;
    },
  });
}

/** Analiz detay düzeninin alt sekmelere verdiği bağlam. */
export interface AnalysisOutletContext {
  run: AnalysisRunDetail;
  source: AnalysisSource;
}

export function useAnalysisContext(): AnalysisOutletContext {
  return useOutletContext<AnalysisOutletContext>();
}

export function useEndpoints(runId: number) {
  return useQuery({ queryKey: queryKeys.demo.analysisRuns.endpoints(runId), queryFn: () => listEndpoints(runId) });
}

export function useGeneratedTests(runId: number) {
  return useQuery({ queryKey: queryKeys.demo.analysisRuns.tests(runId), queryFn: () => listGeneratedTests(runId) });
}

export function useSecurityFindings(runId: number) {
  return useQuery({
    queryKey: queryKeys.demo.analysisRuns.findings(runId),
    queryFn: () => listSecurityFindings(runId),
  });
}

/** Tek seferlik sonuç listesi (bulgu → test eşlemesi gibi canlı olmayan kullanımlar için). */
export function useTestResults(runId: number) {
  return useQuery({ queryKey: queryKeys.demo.analysisRuns.results(runId), queryFn: () => listTestResults(runId) });
}

export function useEvaluation(runId: number) {
  return useQuery({ queryKey: queryKeys.demo.analysisRuns.evaluation(runId), queryFn: () => getEvaluation(runId) });
}

export type StreamState =
  | { status: 'loading' }
  | { status: 'error'; error: ApiError }
  | { status: 'ready'; snapshot: ExecutionSnapshot };

/**
 * Test yürütme akışı. Abonelik bileşen ayrılınca veya analiz değişince kapatılır; StrictMode'daki
 * çift mount yalnızca bir etkin abonelik bırakır (ilk abonelik temizlenir).
 */
export function useExecutionStream(runId: number, intervalMs?: number): StreamState {
  const [state, setState] = useState<StreamState>({ status: 'loading' });
  useEffect(() => {
    setState({ status: 'loading' });
    const unsubscribe = subscribeExecution(
      runId,
      (snapshot) => setState({ status: 'ready', snapshot }),
      (error) => setState({ status: 'error', error }),
      intervalMs === undefined ? {} : { intervalMs },
    );
    return unsubscribe;
  }, [runId, intervalMs]);
  return state;
}
