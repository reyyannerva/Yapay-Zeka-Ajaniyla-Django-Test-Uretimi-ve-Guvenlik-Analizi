import { afterEach, describe, expect, test, vi } from 'vitest';

import type { ExecutionSnapshot } from '../../types';
import {
  buildDemoJsonReport,
  getEvaluation,
  listEndpoints,
  listGeneratedTests,
  prepareReport,
  subscribeExecution,
} from './analysis-results';

afterEach(() => {
  vi.useRealTimers();
});

describe('analiz sonuç servisi (mock)', () => {
  test('bilinmeyen analiz 404 ile reddedilir', async () => {
    await expect(listEndpoints(999)).rejects.toMatchObject({ status: 404 });
  });

  test('dönen diziler kopyadır; fixture değişmez', async () => {
    const a = await listEndpoints(4);
    a[0]!.path = '/degisti/';
    const b = await listEndpoints(4);
    expect(b[0]!.path).toBe('/api/orders/');
  });

  test('her üç üretim yaklaşımına ait veri vardır (kural, LLM, hibrit analiz)', async () => {
    const tests = await listGeneratedTests(4);
    expect(tests.some((t) => t.generation_method === 'RULE_BASED')).toBe(true);
    expect(tests.some((t) => t.generation_method === 'LLM')).toBe(true);
  });

  test('altın etiketli veri yoksa değerlendirme null döner', async () => {
    expect(await getEvaluation(5)).toBeNull();
    expect(await getEvaluation(4)).toMatchObject({ tp: 3, fp: 1, fn: 1 });
  });

  test('canlı akış adım adım ilerler, bitince durur ve abonelik iptali zamanlayıcıyı temizler', async () => {
    vi.useFakeTimers();
    const snapshots: ExecutionSnapshot[] = [];
    const unsubscribe = subscribeExecution(2, (s) => snapshots.push(s), () => {}, { intervalMs: 100 });
    await Promise.resolve();
    expect(snapshots).toHaveLength(1);
    expect(snapshots[0]!.finished).toBe(false);
    vi.advanceTimersByTime(100);
    expect(snapshots).toHaveLength(2);
    vi.advanceTimersByTime(1000);
    const last = snapshots[snapshots.length - 1]!;
    expect(last.finished).toBe(true);
    expect(last.results.every((r) => r.status !== 'PENDING' && r.status !== 'RUNNING')).toBe(true);
    const count = snapshots.length;
    vi.advanceTimersByTime(1000);
    expect(snapshots).toHaveLength(count);
    unsubscribe();
    expect(vi.getTimerCount()).toBe(0);
  });

  test('erken iptal edilen abonelik hiçbir anlık görüntü göndermez', async () => {
    vi.useFakeTimers();
    const onSnapshot = vi.fn();
    const unsubscribe = subscribeExecution(2, onSnapshot, () => {}, { intervalMs: 100 });
    unsubscribe();
    await Promise.resolve();
    vi.advanceTimersByTime(1000);
    expect(onSnapshot).not.toHaveBeenCalled();
    expect(vi.getTimerCount()).toBe(0);
  });

  test('tamamlanmış analiz tek bir son anlık görüntü gönderir', async () => {
    const onSnapshot = vi.fn();
    subscribeExecution(4, onSnapshot, () => {});
    await Promise.resolve();
    expect(onSnapshot).toHaveBeenCalledTimes(1);
    expect(onSnapshot.mock.calls[0]![0].finished).toBe(true);
  });

  test('rapor hazırlama: başarı ve DEMO hata senaryosu', async () => {
    await expect(prepareReport(4, { format: 'JSON', sections: ['ANALYSIS_SUMMARY'] }, 0)).resolves.toMatchObject({
      scope: 'FULL',
      sections: ['ANALYSIS_SUMMARY'],
    });
    await expect(prepareReport(6, { format: 'PDF', sections: ['ANALYSIS_SUMMARY'] }, 0)).rejects.toMatchObject({ status: 500 });
  });

  test('DEMO JSON raporu yalnızca seçilen bölümleri içerir ve DEMO olarak işaretlidir', () => {
    const doc = buildDemoJsonReport(4, ['SECURITY_FINDINGS']);
    expect(doc.demo).toBe(true);
    expect(doc).toHaveProperty('security_findings');
    expect(doc).not.toHaveProperty('generated_tests');
    expect(doc).not.toHaveProperty('evaluation');
  });
});
