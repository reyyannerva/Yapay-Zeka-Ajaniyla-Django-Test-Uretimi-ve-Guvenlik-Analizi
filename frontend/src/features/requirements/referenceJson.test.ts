import { describe, expect, test } from 'vitest';

import { HTTP_METHODS, parseRequirementJson, toEditableJson } from './referenceJson';

const rule = (method: unknown, extra: Record<string, unknown> = {}) => ({
  requirement_code: 'ACC-1',
  category: 'ACCESS_RULE',
  title: 'Kural',
  expected_result: '401',
  specification: { schema_version: 1, endpoint: '/api/x/', method, expected_status_by_role: { anonim: 401 } },
  ...extra,
});

describe('parseRequirementJson', () => {
  test.each(HTTP_METHODS)('%s metodu kabul edilir', (method) => {
    const result = parseRequirementJson(JSON.stringify(rule(method)), 7);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.items[0]).toMatchObject({ project: 7, source: 'JSON_UPLOAD', specification: { method } });
    }
  });

  test('metot backend şemasına göre normalize edilir (" patch " → PATCH)', () => {
    const result = parseRequirementJson(JSON.stringify(rule(' patch ')), 1);
    expect(result.ok && result.items[0]!.specification).toMatchObject({ method: 'PATCH' });
  });

  test.each(['TRACE', 'HEAD', 'OPTIONS', '', 42])('desteklenmeyen metot (%s) reddedilir', (method) => {
    const result = parseRequirementJson(JSON.stringify(rule(method)), 1);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.issues[0]).toMatchObject({ field: 'specification.method' });
  });

  test('geçersiz JSON sözdizimi açıklanır', () => {
    const result = parseRequirementJson('{"requirement_code": ', 1);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.issues[0]!.message).toMatch(/Geçersiz JSON sözdizimi/);
  });

  test('eksik zorunlu alanlar ve yanlış tipler alan bazında raporlanır', () => {
    const result = parseRequirementJson(
      JSON.stringify({ category: 'ACCESS_RULE', specification: { schema_version: 1, endpoint: '', method: 'GET', expected_status_by_role: { anonim: 'x' } }, is_active: 'evet' }),
      1,
    );
    expect(result.ok).toBe(false);
    if (!result.ok) {
      const fields = result.issues.map((i) => i.field);
      expect(fields).toEqual(
        expect.arrayContaining(['requirement_code', 'title', 'expected_result', 'is_active', 'specification.endpoint', 'specification.expected_status_by_role.anonim']),
      );
    }
  });

  test('desteklenmeyen kategori ve alan reddedilir', () => {
    const result = parseRequirementJson(JSON.stringify({ ...rule('GET'), category: 'OTHER', owner: 5 }), 1);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.issues.map((i) => i.field)).toEqual(expect.arrayContaining(['category', 'owner']));
  });

  test('başka projeye ait kimlik gönderilemez (proje açık olan projedir)', () => {
    const result = parseRequirementJson(JSON.stringify(rule('GET', { project: 999 })), 1);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.issues[0]).toMatchObject({ field: 'project' });
  });

  test('dizide yinelenen kod reddedilir; dizideki her kayıt sırasıyla raporlanır', () => {
    const dup = parseRequirementJson(JSON.stringify([rule('GET'), rule('POST')]), 1);
    expect(dup.ok).toBe(false);
    const second = parseRequirementJson(JSON.stringify([rule('GET'), { ...rule('GET'), requirement_code: '#bad' }]), 1);
    expect(!second.ok && second.issues[0]!.index).toBe(2);
  });

  test('ROLE ve DEPLOY_EXPECTATION şemaları', () => {
    expect(parseRequirementJson(JSON.stringify({ requirement_code: 'R1', category: 'ROLE', title: 'Rol', specification: { schema_version: 1, role: 'admin' } }), 1).ok).toBe(true);
    const deploy = parseRequirementJson(JSON.stringify({ requirement_code: 'D1', category: 'DEPLOY_EXPECTATION', title: 'Debug', expected_result: 'kapalı', specification: { schema_version: 1 } }), 1);
    expect(!deploy.ok && deploy.issues.map((i) => i.field)).toEqual(['specification.setting', 'specification.expected_value']);
  });

  test('toEditableJson yalnızca yazılabilir alanları içerir', () => {
    const text = toEditableJson({ requirement_code: 'R1', category: 'ROLE', title: 'Rol', specification: { schema_version: 1, role: 'x' } });
    expect(Object.keys(JSON.parse(text))).toEqual(['requirement_code', 'category', 'title', 'description', 'expected_result', 'specification', 'is_active']);
  });
});
