// Analiz sonuç tipleri (#40). Alan adları backend modelleriyle aynıdır:
// backend/core/models/{endpoint,generation,execution,security,reporting,llm}.py.
// Bu kayıtların REST uçları henüz yoktur (#41); şimdilik `lib/api/mock/` fixture'ları kullanılır.
import type {
  LlmProvider,
  SecurityFindingClassification,
  Severity,
  TestExecutionStatus,
} from './analysis-run';
import type { HttpMethod } from './reference-requirement';

/** Endpoint.unsupported_reason */
export type UnsupportedReason = 'DYNAMIC_ROUTE' | 'CUSTOM_PERMISSION';

/** core.Endpoint — AST analizinde bulunan uç nokta. */
export interface EndpointAnalysis {
  id: number;
  analysis_run: number;
  path: string;
  http_method: HttpMethod;
  view_name: string;
  /** Kimlik doğrulama türü (ör. "Token", "Session"). Boş metin: kaynak koddan belirlenemedi. */
  auth_type: string;
  /** Yetkilendirme (izin) sınıfları. Boş dizi: izin sınıfı belirlenemedi/yok. */
  permission_classes: string[];
  is_supported: boolean;
  unsupported_reason: UnsupportedReason | null;
}

/** GeneratedTest.generation_method — test bazında yöntem (analiz yöntemi HYBRID olabilir). */
export type TestGenerationMethod = 'LLM' | 'RULE_BASED';

/** GeneratedTest.validation_status */
export type TestValidationStatus = 'PENDING' | 'VALID' | 'INVALID_SYNTAX' | 'REJECTED_POLICY';

/**
 * GeneratedTest.generation_metadata içindeki model/fallback alanları.
 * Backend bu JSON'u serbest biçimde saklar; burada yalnızca ekranın okuduğu alanlar tiplenir.
 * Alan yoksa arayüz "bilinmiyor" gösterir, varsayım yapmaz.
 */
export interface GenerationMetadata {
  requested_provider?: LlmProvider;
  requested_model?: string;
  provider?: LlmProvider;
  model?: string;
  fallback_used?: boolean;
  /** Fallback nedeni (ör. sağlayıcı kotası). */
  fallback_reason?: string;
  prompt_version?: string;
}

/** core.GeneratedTest */
export interface GeneratedTest {
  id: number;
  analysis_run: number;
  /** İlgili endpoint (yapılandırma testlerinde null olabilir). */
  endpoint: number | null;
  test_module: string;
  test_name: string;
  generation_method: TestGenerationMethod;
  requirement_code: string;
  role: string;
  expected_status: number | null;
  is_security_test: boolean;
  /** Üretilen Pytest kaynağı. Güvenilmeyen metindir; yalnızca düz metin olarak gösterilir. */
  source_code: string;
  code_sha256: string;
  validation_status: TestValidationStatus;
  validation_errors: string[];
  repair_count: number;
  generation_metadata: GenerationMetadata;
}

/** TestExecution.error_type */
export type ExecutionErrorType = 'IMPORT' | 'FIXTURE' | 'SYNTAX' | 'TIMEOUT' | 'OOM' | 'OTHER';
/** TestExecution.error_origin */
export type ExecutionErrorOrigin = 'TEST_CODE' | 'TARGET_APP' | 'INFRASTRUCTURE';

/** core.TestExecution — bir testin son yürütme denemesi. */
export interface TestExecutionResult {
  id: number;
  generated_test: number;
  attempt_number: number;
  status: TestExecutionStatus;
  observed_status: number | null;
  error_type: ExecutionErrorType | null;
  error_origin: ExecutionErrorOrigin | null;
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
  /** Çıktı kesiti (en fazla 10 000 karakter). Güvenilmeyen metin. */
  output_excerpt: string;
  error_summary: string;
}

/** SecurityFinding.source */
export type FindingSource = 'AUTH_TEST' | 'BANDIT' | 'CHECK_DEPLOY';

/** core.SecurityFinding */
export interface SecurityFinding {
  id: number;
  analysis_run: number;
  test_execution: number | null;
  endpoint: number | null;
  source: FindingSource;
  rule_id: string;
  severity: Severity;
  classification: SecurityFindingClassification;
  title: string;
  description: string;
  file_path: string;
  line_number: number | null;
  /** Kanıt kesiti. Boş metin: kanıt kaydı yok. */
  evidence_excerpt: string;
  /** Düzeltme önerisi anahtarı; metin `lib/recommendations.ts` kataloğundadır. */
  recommendation_key: string | null;
}

/**
 * Güvenlik tespit değerlendirmesi (H3-06 yöntemi). Test PASS/FAIL sayımlarından ayrıdır:
 * altın etiketli referans kümesiyle karşılaştırmadan elde edilir.
 */
export interface EvaluationCounts {
  tp: number;
  fp: number;
  fn: number;
  tn: number;
  /** Karşılaştırmanın yapıldığı referans küme (ör. "reference_cases/test_set.json"). */
  ground_truth: string;
}

/** Rapor bölümleri (Report.sections). */
export type ReportSection =
  | 'ANALYSIS_SUMMARY'
  | 'GENERATED_TESTS'
  | 'EXECUTION_RESULTS'
  | 'SECURITY_FINDINGS'
  | 'EVALUATION_METRICS';

/** Report.format */
export type ReportFormat = 'PDF' | 'JSON';
/** Report.scope */
export type ReportScope = 'FULL' | 'PARTIAL';

/** Rapor isteğinin arayüz durumu. */
export type ReportStatus = 'idle' | 'preparing' | 'ready' | 'error';

/** core.Report — hazırlanmış rapor kaydı. */
export interface ReportRecord {
  id: number;
  analysis_run: number;
  format: ReportFormat;
  scope: ReportScope;
  sections: ReportSection[];
  file_size_bytes: number;
  created_at: string;
}

/** Canlı yürütme akışının bir anlık görüntüsü (sıra test kimliğine göredir). */
export interface ExecutionSnapshot {
  results: TestExecutionResult[];
  /** Akış bitti mi (tüm testler uç durumda veya akış durduruldu). */
  finished: boolean;
}
