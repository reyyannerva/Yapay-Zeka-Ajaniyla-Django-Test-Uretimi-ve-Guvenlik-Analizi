// Kanonik durum enum'ları → etiket / ton eşlemesi (docs/database + docs/api/analysis.md).
// Tonlar tema token'larına bağlıdır (bkz. StatusBadge.tsx); burada renk değeri yazılmaz.
import type {
  AnalysisRunStatus,
  SecurityFindingClassification,
  Severity,
  TestExecutionStatus,
} from '../types';

export type RunTone = 'pass' | 'process' | 'error' | 'muted';
export type TestTone = 'pass' | 'fail' | 'error' | 'timeout' | 'process' | 'muted';
export type FindingTone = 'error' | 'fail' | 'muted';

export const STATUS_META: Record<AnalysisRunStatus, { label: string; tone: RunTone }> = {
  QUEUED: { label: 'Kuyrukta', tone: 'muted' },
  ANALYZING: { label: 'Analiz ediliyor', tone: 'process' },
  GENERATING: { label: 'Test üretiliyor', tone: 'process' },
  VALIDATING: { label: 'Doğrulanıyor', tone: 'process' },
  EXECUTING: { label: 'Çalıştırılıyor', tone: 'process' },
  SCANNING: { label: 'Taranıyor', tone: 'process' },
  COMPLETED: { label: 'Tamamlandı', tone: 'pass' },
  FAILED: { label: 'Başarısız', tone: 'error' },
  CANCELLED: { label: 'İptal edildi', tone: 'muted' },
};

// ERROR (çalıştırma hatası) ile TIMEOUT (zaman aşımı) ayrı kavramlardır; ayrı ton alır.
export const TEST_STATUS_META: Record<TestExecutionStatus, { label: string; tone: TestTone }> = {
  PENDING: { label: 'Bekliyor', tone: 'muted' },
  RUNNING: { label: 'Çalışıyor', tone: 'process' },
  PASS: { label: 'Geçti', tone: 'pass' },
  FAIL: { label: 'Kaldı', tone: 'fail' },
  ERROR: { label: 'Hata', tone: 'error' },
  TIMEOUT: { label: 'Zaman aşımı', tone: 'timeout' },
  STOPPED: { label: 'Durduruldu', tone: 'muted' },
  NOT_RUN: { label: 'Çalıştırılmadı', tone: 'muted' },
};

// VERIFIED doğrulanmış AÇIK bir bulgudur: asla başarı (yeşil) tonu almaz.
export const FINDING_META: Record<
  SecurityFindingClassification,
  { label: string; tone: FindingTone }
> = {
  VERIFIED: { label: 'Doğrulanmış', tone: 'error' },
  POSSIBLE: { label: 'Olası', tone: 'fail' },
  UNCERTAIN: { label: 'Belirsiz', tone: 'muted' },
};

export const SEVERITY_LABEL: Record<Severity, string> = {
  HIGH: 'Yüksek',
  MEDIUM: 'Orta',
  LOW: 'Düşük',
  UNKNOWN: 'Bilinmiyor',
};

/** Bulgu tonu: doğrulanmış düşük önem derecesi uyarı (amber), diğer doğrulananlar kırmızı. */
export function findingTone(
  classification: SecurityFindingClassification,
  severity?: Severity,
): FindingTone {
  if (classification === 'VERIFIED' && severity === 'LOW') return 'fail';
  return FINDING_META[classification].tone;
}

export interface StageNode {
  key: AnalysisRunStatus;
  label: string;
}

/** Kanonik aşamalar; son düğüm COMPLETED'dır ("Rapor" aşaması yoktur). */
export const STAGES: readonly StageNode[] = [
  { key: 'QUEUED', label: 'Kuyruk' },
  { key: 'ANALYZING', label: 'Analiz' },
  { key: 'GENERATING', label: 'Üretim' },
  { key: 'EXECUTING', label: 'Çalıştırma' },
  { key: 'SCANNING', label: 'Tarama' },
  { key: 'COMPLETED', label: 'Tamamlandı' },
];

/** VALIDATING, üretim aşamasının alt adımıdır; şeritte "Üretim" düğümüne bağlanır. */
export function stageIndex(status: AnalysisRunStatus): number {
  if (status === 'VALIDATING') return STAGES.findIndex((s) => s.key === 'GENERATING');
  return STAGES.findIndex((s) => s.key === status);
}
