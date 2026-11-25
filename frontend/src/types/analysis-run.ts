// docs/api/analysis.md + docs/database (kanonik enum değerleri)
export type AnalysisRunStatus =
  | 'QUEUED'
  | 'ANALYZING'
  | 'GENERATING'
  | 'VALIDATING'
  | 'EXECUTING'
  | 'SCANNING'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED';

export type AnalysisMethod = 'RULE_BASED' | 'DIRECT_LLM' | 'HYBRID';
export type LlmProvider = 'GROQ' | 'GEMINI' | 'OLLAMA';

export type TestExecutionStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'PASS'
  | 'FAIL'
  | 'ERROR'
  | 'TIMEOUT'
  | 'STOPPED'
  | 'NOT_RUN';

export type SecurityFindingClassification = 'VERIFIED' | 'POSSIBLE' | 'UNCERTAIN';
export type Severity = 'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN';

/** Yalnızca detay/oluşturma yanıtında bulunur; TestExecution kayıtlarından türetilir. */
export interface AnalysisProgress {
  total: number;
  completed: number;
  running: number;
  pending: number;
  by_status: Partial<Record<TestExecutionStatus, number>>;
  completed_duration_ms_total: number;
  completed_with_duration: number;
  run_started_at: string | null;
  /** Henüz yürütme kaydı yoksa null (0 değil). */
  percent: number | null;
}

/** GET /api/analysis-runs/ satırı (AnalysisRunList). */
export interface AnalysisRun {
  id: number;
  /** Proje kimliği */
  project: number;
  status: AnalysisRunStatus;
  method: AnalysisMethod;
  llm_provider: LlmProvider | null;
  llm_model: string | null;
  fallback_enabled: boolean;
  celery_task_id: string | null;
  /** Ondalık metin (ör. "12.50") veya null */
  coverage_percent: string | null;
  error_code: string;
  error_message: string;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  updated_at: string;
}

/** GET /api/analysis-runs/{id}/ (AnalysisRunDetail). */
export interface AnalysisRunDetail extends AnalysisRun {
  requirements_snapshot: Record<string, unknown>[];
  generated_test_count: number;
  progress: AnalysisProgress;
}
