import { describe, expect, test } from 'vitest';

import { mockRunResults } from '../../lib/api/mock/analysis-results';
import type { TestExecutionResult, TestExecutionStatus } from '../../types';
import { EMPTY_FILTERS, filterEndpoints } from './EndpointsPage';
import { diffLines } from './LiveOutput';

const E4 = mockRunResults[4]!.endpoints;

describe('filterEndpoints', () => {
  test('boş filtre tümünü döndürür', () => {
    expect(filterEndpoints(E4, EMPTY_FILTERS)).toHaveLength(E4.length);
  });
  test('birden çok metot birleşimle (VEYA) filtrelenir', () => {
    const r = filterEndpoints(E4, { ...EMPTY_FILTERS, methods: ['PUT', 'PATCH'] });
    expect(r.map((e) => e.http_method).sort()).toEqual(['PATCH', 'PUT']);
  });
  test('arama yol ve view adında büyük/küçük harf duyarsız çalışır', () => {
    expect(filterEndpoints(E4, { ...EMPTY_FILTERS, query: 'userlist' })).toHaveLength(1);
    expect(filterEndpoints(E4, { ...EMPTY_FILTERS, query: '  /API/ORDERS/ ' }).length).toBeGreaterThan(0);
  });
  test('izin sınıfı ve kapsam filtreleri', () => {
    expect(filterEndpoints(E4, { ...EMPTY_FILTERS, permission: 'IsAdminUser' })).toHaveLength(1);
    expect(filterEndpoints(E4, { ...EMPTY_FILTERS, support: 'unsupported' })).toHaveLength(2);
    expect(filterEndpoints(mockRunResults[6]!.endpoints, { ...EMPTY_FILTERS, permission: '__none__' })).toHaveLength(1);
  });
});

function r(testId: number, status: TestExecutionStatus): TestExecutionResult {
  return { ...mockRunResults[4]!.results()[0]!, generated_test: testId, status, error_summary: '', observed_status: null };
}

describe('diffLines', () => {
  test('yalnızca durumu değişen ve PENDING olmayan testler için satır üretir', () => {
    const prev = new Map<number, TestExecutionStatus>([[1, 'RUNNING'], [2, 'PENDING']]);
    const lines = diffLines(prev, [r(1, 'PASS'), r(2, 'PENDING'), r(3, 'RUNNING')], (id) => `t${id}`, 10);
    expect(lines.map((l) => [l.seq, l.testId, l.status])).toEqual([
      [10, 1, 'PASS'],
      [11, 3, 'RUNNING'],
    ]);
    expect(lines[1]!.text).toBe('t3 başladı');
  });
  test('değişiklik yoksa satır yok', () => {
    const prev = new Map<number, TestExecutionStatus>([[1, 'PASS']]);
    expect(diffLines(prev, [r(1, 'PASS')], String, 0)).toEqual([]);
  });
});
