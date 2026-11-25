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
import { queryKeys } from '../../lib/queryKeys';
import type { AnalysisRunDetail, ApiError, ExecutionSnapshot } from '../../types';

/** URL'deki :id değerini doğrular; geçersizse null. */
export function useRunId(): number | null {
  const { id } = useParams();
  const parsed = Number(id);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

export function useAnalysisRun(runId: number | null) {
  return useQuery({
    queryKey: queryKeys.analysisRuns.detail(runId ?? 0),
    queryFn: () => getAnalysisRun(runId as number),
    enabled: runId !== null,
  });
}

/** Analiz detay düzeninin alt sekmelere verdiği bağlam. */
export interface AnalysisOutletContext {
  run: AnalysisRunDetail;
}

export function useAnalysisContext(): AnalysisOutletContext {
  return useOutletContext<AnalysisOutletContext>();
}

export function useEndpoints(runId: number) {
  return useQuery({ queryKey: queryKeys.analysisRuns.endpoints(runId), queryFn: () => listEndpoints(runId) });
}

export function useGeneratedTests(runId: number) {
  return useQuery({ queryKey: queryKeys.analysisRuns.tests(runId), queryFn: () => listGeneratedTests(runId) });
}

export function useSecurityFindings(runId: number) {
  return useQuery({
    queryKey: queryKeys.analysisRuns.findings(runId),
    queryFn: () => listSecurityFindings(runId),
  });
}

/** Tek seferlik sonuç listesi (bulgu → test eşlemesi gibi canlı olmayan kullanımlar için). */
export function useTestResults(runId: number) {
  return useQuery({ queryKey: queryKeys.analysisRuns.results(runId), queryFn: () => listTestResults(runId) });
}

export function useEvaluation(runId: number) {
  return useQuery({ queryKey: queryKeys.analysisRuns.evaluation(runId), queryFn: () => getEvaluation(runId) });
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
