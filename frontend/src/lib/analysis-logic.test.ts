import { describe, expect, test } from 'vitest';

import { computeProgress, estimateRemaining, formatDuration, formatPercent, isTerminalTestStatus } from './execution-progress';
import { NOT_MEASURABLE, f1, formatMetric, precision, ratio, recall, summarize } from './evaluation-metrics';
import { getRecommendation } from './recommendations';
import { canPrepareReport, reportFileName, reportScopeFor, toggleSection, validateSelection } from './report-sections';

describe('computeProgress', () => {
  test('uç durumlar tamamlanmış, PENDING/RUNNING tamamlanmamış sayılır', () => {
    const p = computeProgress(['PASS', 'FAIL', 'ERROR', 'TIMEOUT', 'RUNNING', 'PENDING', 'PENDING', 'NOT_RUN']);
    expect(p.total).toBe(8);
    expect(p.completed).toBe(5);
    expect(p.running).toBe(1);
    expect(p.pending).toBe(2);
    expect(p.percent).toBe(62.5);
    expect(p.byStatus.ERROR).toBe(1);
    expect(p.byStatus.TIMEOUT).toBe(1);
  });

  test('hiç test yoksa yüzde null olur (0 ile doldurulmaz)', () => {
    expect(computeProgress([]).percent).toBeNull();
    expect(formatPercent(null)).toBe('—');
  });

  test('bilinmeyen durum sayıma katılmaz ve yüzde 0–100 aralığında kalır', () => {
    const p = computeProgress(['PASS', 'WEIRD' as never]);
    expect(p.byStatus.PASS).toBe(1);
    expect(p.percent).toBeGreaterThanOrEqual(0);
    expect(p.percent).toBeLessThanOrEqual(100);
  });

  test('ERROR ve TIMEOUT ayrı uç durumlardır; RUNNING uç değildir', () => {
    expect(isTerminalTestStatus('ERROR')).toBe(true);
    expect(isTerminalTestStatus('TIMEOUT')).toBe(true);
    expect(isTerminalTestStatus('RUNNING')).toBe(false);
  });
});

describe('estimateRemaining', () => {
  test('yeterli örnek yoksa tahmin üretilmez', () => {
    expect(estimateRemaining({ completedDurationMsTotal: 200, completedWithDuration: 2, remaining: 5 }).kind).toBe('unknown');
  });
  test('ortalama süre × kalan test', () => {
    expect(estimateRemaining({ completedDurationMsTotal: 400, completedWithDuration: 4, remaining: 6 })).toEqual({ kind: 'estimate', ms: 600 });
  });
  test('kalan test yoksa "done"', () => {
    expect(estimateRemaining({ completedDurationMsTotal: 0, completedWithDuration: 0, remaining: 0 }).kind).toBe('done');
  });
  test('geçersiz süre verisi tahmin üretmez', () => {
    expect(estimateRemaining({ completedDurationMsTotal: -500, completedWithDuration: 5, remaining: 2 }).kind).toBe('unknown');
  });
  test('süre biçimi', () => {
    expect(formatDuration(850)).toBe('850 ms');
    expect(formatDuration(4200)).toBe('4,2 sn');
    expect(formatDuration(132_000)).toBe('2 dk 12 sn');
    expect(formatDuration(null)).toBe('—');
  });
});

describe('değerlendirme metrikleri', () => {
  test('payda sıfırsa ölçülemez (null), 0 veya 1 ile doldurulmaz', () => {
    expect(ratio(0, 0)).toBeNull();
    expect(precision({ tp: 0, fp: 0 })).toBeNull();
    expect(recall({ tp: 0, fn: 0 })).toBeNull();
    expect(formatMetric(null)).toBe(NOT_MEASURABLE);
  });
  test('negatif sayım reddedilir', () => {
    expect(() => ratio(-1, 2)).toThrow(RangeError);
  });
  test('F1: P veya R yoksa ya da P + R = 0 ise ölçülemez', () => {
    expect(f1(null, 0.5)).toBeNull();
    expect(f1(0, 0)).toBeNull();
    expect(f1(0.75, 0.75)).toBeCloseTo(0.75);
  });
  test('summarize TP/FP/FN değerlerinden hesaplar', () => {
    const s = summarize({ tp: 3, fp: 1, fn: 1, tn: 7, ground_truth: 'x' });
    expect(s.precision).toBeCloseTo(0.75);
    expect(s.recall).toBeCloseTo(0.75);
    expect(formatMetric(s.f1)).toBe('0,75');
  });
});

describe('rapor bölümleri', () => {
  test('toggle kanonik sırayı korur', () => {
    expect(toggleSection(['SECURITY_FINDINGS'], 'ANALYSIS_SUMMARY')).toEqual(['ANALYSIS_SUMMARY', 'SECURITY_FINDINGS']);
    expect(toggleSection(['ANALYSIS_SUMMARY', 'SECURITY_FINDINGS'], 'ANALYSIS_SUMMARY')).toEqual(['SECURITY_FINDINGS']);
  });
  test('boş seçim ve değerlendirme verisi olmadan metrik bölümü geçersizdir', () => {
    expect(validateSelection([], { hasEvaluation: true })).not.toBeNull();
    expect(validateSelection(['EVALUATION_METRICS'], { hasEvaluation: false })).not.toBeNull();
    expect(validateSelection(['EVALUATION_METRICS'], { hasEvaluation: true })).toBeNull();
  });
  test('kapsam ve hazırlanabilirlik', () => {
    expect(reportScopeFor('COMPLETED')).toBe('FULL');
    expect(reportScopeFor('FAILED')).toBe('PARTIAL');
    expect(canPrepareReport('EXECUTING')).toBe(false);
    expect(canPrepareReport('FAILED')).toBe(true);
  });
  test('dosya adı yalnızca güvenli karakter içerir', () => {
    expect(reportFileName(4, 'JSON')).toBe('testkalkan-analiz-4-rapor-demo.json');
    expect(reportFileName(Number.NaN, 'PDF')).toBe('testkalkan-analiz-0-rapor-demo.pdf');
    expect(reportFileName(-3, 'PDF')).toMatch(/^[a-z0-9.-]+$/);
  });
});

describe('düzeltme önerileri', () => {
  test('bilinen anahtar başlık, metin ve referans döndürür; bilinmeyen/boş anahtar null', () => {
    const r = getRecommendation('OBJECT_LEVEL_AUTHZ');
    expect(r?.title).toBeTruthy();
    expect(r?.reference).toBeTruthy();
    expect(getRecommendation('YOK')).toBeNull();
    expect(getRecommendation(null)).toBeNull();
  });
});
