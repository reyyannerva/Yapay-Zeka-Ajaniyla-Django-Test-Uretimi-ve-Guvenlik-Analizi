// Analiz çalıştırması servisi (H5-03 / #41) — backend/core/api (AnalysisRunViewSet).
// Oluşturma yalnızca QUEUED durumunda bir kayıt açar; analiz motoru bu sürümde tetiklenmez.
import type { AnalysisMethod, AnalysisRun, AnalysisRunDetail, LlmProvider } from '../../types';
import { apiFetch } from './client';

/** GET /api/analysis-runs/ — 200, kullanıcının tüm analizleri (sayfalama yok), en yeni önce. */
export function listAnalysisRuns(signal?: AbortSignal): Promise<AnalysisRun[]> {
  return apiFetch<AnalysisRun[]>('/api/analysis-runs/', { signal });
}

/** GET /api/analysis-runs/{id}/ — 200 (ilerleme dahil); yoksa veya başkasına aitse 404. */
export function getAnalysisRun(id: number, signal?: AbortSignal): Promise<AnalysisRunDetail> {
  return apiFetch<AnalysisRunDetail>(`/api/analysis-runs/${id}/`, { signal });
}

export interface AnalysisRunCreateInput {
  project: number;
  method: AnalysisMethod;
  /** RULE_BASED'de gönderilmez; LLM yöntemlerinde zorunlu. */
  llm_provider?: LlmProvider | null;
  llm_model?: string | null;
  fallback_enabled?: boolean;
}

/** POST /api/analysis-runs/ — 201 (detay); başkasının projesi 400 `project` (varlık ifşa edilmez). */
export function createAnalysisRun(input: AnalysisRunCreateInput): Promise<AnalysisRunDetail> {
  const body: Record<string, unknown> = {
    project: input.project,
    method: input.method,
    fallback_enabled: input.fallback_enabled ?? true,
  };
  if (input.method !== 'RULE_BASED') {
    body.llm_provider = input.llm_provider ?? null;
    body.llm_model = input.llm_model ?? null;
  }
  return apiFetch<AnalysisRunDetail>('/api/analysis-runs/', { method: 'POST', body });
}
