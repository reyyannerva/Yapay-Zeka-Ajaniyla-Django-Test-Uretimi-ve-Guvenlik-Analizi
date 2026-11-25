// Güvenlik tespit değerlendirme metrikleri (#40). Tanımlar agent/evaluation/metrics.py ile aynıdır:
// payda sıfırsa değer ölçülemez (null) ve "Ölçülemedi" yazılır; 0 veya 1 ile doldurulmaz.
// Bu metrikler test yürütme sonuçlarından (PASS/FAIL/ERROR/TIMEOUT) türetilmez; altın etiketli
// referans kümesiyle karşılaştırmadan (TP/FP/FN) gelir.
import type { EvaluationCounts } from '../types';

export const NOT_MEASURABLE = 'Ölçülemedi';

export function ratio(numerator: number, denominator: number): number | null {
  if (numerator < 0 || denominator < 0) throw new RangeError('Negatif sayım');
  return denominator === 0 ? null : numerator / denominator;
}

/** Precision = TP / (TP + FP) */
export function precision(c: Pick<EvaluationCounts, 'tp' | 'fp'>): number | null {
  return ratio(c.tp, c.tp + c.fp);
}

/** Recall = TP / (TP + FN) */
export function recall(c: Pick<EvaluationCounts, 'tp' | 'fn'>): number | null {
  return ratio(c.tp, c.tp + c.fn);
}

/** F1 = 2PR / (P + R); P veya R ölçülemiyorsa ya da P + R = 0 ise ölçülemez. */
export function f1(p: number | null, r: number | null): number | null {
  if (p === null || r === null) return null;
  if (p + r === 0) return null;
  return (2 * p * r) / (p + r);
}

export interface EvaluationSummary {
  precision: number | null;
  recall: number | null;
  f1: number | null;
}

export function summarize(c: EvaluationCounts): EvaluationSummary {
  const p = precision(c);
  const r = recall(c);
  return { precision: p, recall: r, f1: f1(p, r) };
}

/** 0–1 arası oranı iki ondalıkla gösterir (ör. "0,75"); ölçülemiyorsa "Ölçülemedi". */
export function formatMetric(value: number | null): string {
  if (value === null) return NOT_MEASURABLE;
  return value.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
