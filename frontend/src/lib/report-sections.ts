// Rapor bölümü seçimi (#40). Bölüm anahtarları Report.sections dizisine yazılan değerlerdir.
import type { AnalysisRunStatus, ReportScope, ReportSection } from '../types';

export interface ReportSectionMeta {
  key: ReportSection;
  label: string;
  description: string;
}

export const REPORT_SECTIONS: readonly ReportSectionMeta[] = [
  { key: 'ANALYSIS_SUMMARY', label: 'Analiz özeti', description: 'Proje, yöntem, model ve aşama bilgileri' },
  { key: 'GENERATED_TESTS', label: 'Üretilen testler', description: 'Test listesi, yöntem ve doğrulama durumu' },
  { key: 'EXECUTION_RESULTS', label: 'Test yürütme sonuçları', description: 'PASS / FAIL / ERROR / TIMEOUT ayrıntıları' },
  { key: 'SECURITY_FINDINGS', label: 'Güvenlik bulguları', description: 'Sınıflandırma, önem derecesi, kanıt ve öneriler' },
  { key: 'EVALUATION_METRICS', label: 'Değerlendirme metrikleri', description: 'Precision, Recall, F1 (altın etiketli referansla)' },
];

export function toggleSection(selected: readonly ReportSection[], key: ReportSection): ReportSection[] {
  return selected.includes(key)
    ? selected.filter((s) => s !== key)
    : REPORT_SECTIONS.map((s) => s.key).filter((k) => k === key || selected.includes(k));
}

export interface SelectionContext {
  /** Değerlendirme verisi (altın etiket karşılaştırması) var mı. */
  hasEvaluation: boolean;
}

/** Seçimin neden geçersiz olduğunu döndürür; geçerliyse null. */
export function validateSelection(
  selected: readonly ReportSection[],
  ctx: SelectionContext,
): string | null {
  if (selected.length === 0) return 'Rapora en az bir bölüm ekleyin.';
  if (selected.includes('EVALUATION_METRICS') && !ctx.hasEvaluation) {
    return 'Bu analiz için değerlendirme verisi yok; "Değerlendirme metrikleri" bölümü eklenemez.';
  }
  return null;
}

/** Tamamlanmamış analizin raporu kısmi (PARTIAL) olur. */
export function reportScopeFor(status: AnalysisRunStatus): ReportScope {
  return status === 'COMPLETED' ? 'FULL' : 'PARTIAL';
}

/** Rapor hazırlanabilecek analiz durumları: tamamlanmış ya da sonuçlanmış (kısmi sonuçlu) analizler. */
export function canPrepareReport(status: AnalysisRunStatus): boolean {
  return status === 'COMPLETED' || status === 'FAILED' || status === 'CANCELLED';
}

/** İndirme dosya adı: yalnızca güvenli karakterler. */
export function reportFileName(runId: number, format: 'PDF' | 'JSON'): string {
  const safeId = Number.isInteger(runId) && runId > 0 ? runId : 0;
  return `testkalkan-analiz-${safeId}-rapor-demo.${format.toLowerCase()}`;
}
