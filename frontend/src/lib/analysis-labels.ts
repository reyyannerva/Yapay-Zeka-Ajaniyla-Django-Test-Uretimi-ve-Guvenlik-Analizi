// Analiz sonuç ekranlarının (#40) enum → Türkçe etiket eşlemeleri. API değerleri değişmez,
// yalnızca görüntülenen metin buradan gelir. Renk/ton eşlemeleri analysis-status.ts'tedir.
import type {
  AnalysisMethod,
  ExecutionErrorOrigin,
  ExecutionErrorType,
  FindingSource,
  LlmProvider,
  TestGenerationMethod,
  TestValidationStatus,
  UnsupportedReason,
} from '../types';
import type { TestTone } from './analysis-status';

export const METHOD_LABEL: Record<AnalysisMethod, string> = {
  RULE_BASED: 'Kural tabanlı',
  DIRECT_LLM: 'LLM tabanlı',
  HYBRID: 'Hibrit',
};

export const TEST_METHOD_LABEL: Record<TestGenerationMethod, string> = {
  RULE_BASED: 'Kural tabanlı',
  LLM: 'LLM',
};

export const PROVIDER_LABEL: Record<LlmProvider, string> = {
  GROQ: 'Groq',
  GEMINI: 'Gemini',
  OLLAMA: 'Ollama',
};

/**
 * Sözdizimi/politika doğrulaması, testin çalıştırılıp geçtiği anlamına gelmez.
 * Bu yüzden VALID bile "pass" (yeşil) tonu almaz; nötr süreç tonu alır.
 */
export const VALIDATION_META: Record<TestValidationStatus, { label: string; tone: TestTone }> = {
  PENDING: { label: 'Doğrulama bekliyor', tone: 'muted' },
  VALID: { label: 'Sözdizimi ve politika uygun', tone: 'process' },
  INVALID_SYNTAX: { label: 'Sözdizimi geçersiz', tone: 'error' },
  REJECTED_POLICY: { label: 'Politika nedeniyle reddedildi', tone: 'fail' },
};

export const FINDING_SOURCE_LABEL: Record<FindingSource, string> = {
  AUTH_TEST: 'Yetkilendirme testi',
  BANDIT: 'Bandit (statik analiz)',
  CHECK_DEPLOY: 'manage.py check --deploy',
};

export const UNSUPPORTED_REASON_LABEL: Record<UnsupportedReason, string> = {
  DYNAMIC_ROUTE: 'Dinamik rota',
  CUSTOM_PERMISSION: 'Özel izin sınıfı',
};

export const ERROR_TYPE_LABEL: Record<ExecutionErrorType, string> = {
  IMPORT: 'İçe aktarma hatası',
  FIXTURE: 'Fixture hatası',
  SYNTAX: 'Sözdizimi hatası',
  TIMEOUT: 'Zaman aşımı',
  OOM: 'Bellek aşımı',
  OTHER: 'Diğer',
};

export const ERROR_ORIGIN_LABEL: Record<ExecutionErrorOrigin, string> = {
  TEST_CODE: 'Üretilen test kodu',
  TARGET_APP: 'Hedef uygulama',
  INFRASTRUCTURE: 'Altyapı',
};
