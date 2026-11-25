// Test yürütme ilerlemesinin tek hesaplama noktası (#40).
// Tanımlar backend/core/progress.py ile aynıdır: bir test, son denemesi uç durumdaysa "tamamlanmış"
// sayılır (PASS, FAIL, ERROR, TIMEOUT ve backend'in STOPPED/NOT_RUN uç durumları).
// PENDING ve RUNNING tamamlanmış sayılmaz. Bu ilerleme, analiz aşamasından (AnalysisRun.status) ayrıdır.
import type { TestExecutionStatus } from '../types';

export const TERMINAL_TEST_STATUSES: readonly TestExecutionStatus[] = [
  'PASS',
  'FAIL',
  'ERROR',
  'TIMEOUT',
  'STOPPED',
  'NOT_RUN',
];

export function isTerminalTestStatus(status: TestExecutionStatus): boolean {
  return TERMINAL_TEST_STATUSES.includes(status);
}

export interface ExecutionProgress {
  total: number;
  completed: number;
  running: number;
  pending: number;
  byStatus: Record<TestExecutionStatus, number>;
  /** 0–100 arası; hiç test yoksa null (0 ile doldurulmaz). */
  percent: number | null;
}

export function emptyStatusCounts(): Record<TestExecutionStatus, number> {
  return { PENDING: 0, RUNNING: 0, PASS: 0, FAIL: 0, ERROR: 0, TIMEOUT: 0, STOPPED: 0, NOT_RUN: 0 };
}

export function computeProgress(statuses: readonly TestExecutionStatus[]): ExecutionProgress {
  const byStatus = emptyStatusCounts();
  for (const status of statuses) {
    // Bilinmeyen bir durum gelirse sayıma katılmaz; arayüz çökmez.
    if (status in byStatus) byStatus[status] += 1;
  }
  const total = statuses.length;
  const completed = TERMINAL_TEST_STATUSES.reduce((sum, s) => sum + byStatus[s], 0);
  const raw = total === 0 ? null : (completed / total) * 100;
  const percent = raw === null ? null : Math.min(100, Math.max(0, Math.round(raw * 10) / 10));
  return { total, completed, running: byStatus.RUNNING, pending: byStatus.PENDING, byStatus, percent };
}

/** Tahmin için gereken en az tamamlanmış ve süresi bilinen test sayısı. */
export const MIN_SAMPLES_FOR_ESTIMATE = 3;

export type RemainingEstimate =
  | { kind: 'done' }
  | { kind: 'unknown'; reason: string }
  | { kind: 'estimate'; ms: number };

export interface EstimateInput {
  /** Süresi bilinen tamamlanmış testlerin toplam süresi (ms). */
  completedDurationMsTotal: number;
  /** Süresi bilinen tamamlanmış test sayısı. */
  completedWithDuration: number;
  /** Henüz bitmemiş (çalışan + bekleyen) test sayısı. */
  remaining: number;
}

/**
 * Kalan süre TAHMİNİ: tamamlanan testlerin ortalama süresi × kalan test sayısı.
 * Testlerin sırayla çalıştığı varsayılır; kesin bitiş zamanı değildir.
 * Yeterli veri yoksa veya sonuç anlamsızsa "unknown" döner (negatif/NaN gösterilmez).
 */
export function estimateRemaining(input: EstimateInput): RemainingEstimate {
  const { completedDurationMsTotal, completedWithDuration, remaining } = input;
  if (remaining <= 0) return { kind: 'done' };
  if (completedWithDuration < MIN_SAMPLES_FOR_ESTIMATE) {
    return { kind: 'unknown', reason: 'Tahmin için yeterli tamamlanmış test yok' };
  }
  const ms = (completedDurationMsTotal / completedWithDuration) * remaining;
  if (!Number.isFinite(ms) || ms < 0) {
    return { kind: 'unknown', reason: 'Süre verisi geçersiz' };
  }
  return { kind: 'estimate', ms };
}

/** Süreyi Türkçe biçimler: "850 ms", "4,2 sn", "2 dk 12 sn". */
export function formatDuration(ms: number | null): string {
  if (ms === null || !Number.isFinite(ms) || ms < 0) return '—';
  if (ms < 1000) return `${Math.round(ms)} ms`;
  const seconds = ms / 1000;
  if (seconds < 60) {
    return `${seconds.toLocaleString('tr-TR', { maximumFractionDigits: 1 })} sn`;
  }
  const total = Math.round(seconds);
  const minutes = Math.floor(total / 60);
  const rest = total % 60;
  return rest === 0 ? `${minutes} dk` : `${minutes} dk ${rest} sn`;
}

export function formatPercent(percent: number | null): string {
  return percent === null ? '—' : `%${percent.toLocaleString('tr-TR', { maximumFractionDigits: 1 })}`;
}
