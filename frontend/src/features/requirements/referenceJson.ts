// Referans gereksinim JSON'unun istemci tarafı ön doğrulaması (H5-03 / #41).
// Kurallar backend/core/serializers.py ve core/models/requirement.py ile aynıdır; amaç kullanıcıya hatayı
// hızlı göstermektir. Asıl doğrulama sunucudadır ve sunucu hataları ayrıca gösterilir.
import type { HttpMethod, ReferenceRequirementInput, RequirementCategory } from '../../types';

export const HTTP_METHODS: readonly HttpMethod[] = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'];
export const CATEGORIES: readonly RequirementCategory[] = ['ROLE', 'ACCESS_RULE', 'DEPLOY_EXPECTATION'];
const CODE_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;
const ALLOWED_KEYS = new Set([
  'requirement_code',
  'category',
  'title',
  'description',
  'expected_result',
  'specification',
  'is_active',
  'source',
]);

export interface RequirementIssue {
  /** Dizi girdisinde kaçıncı kayıt (1'den başlar); tek nesnede 1. */
  index: number;
  /** Alan yolu, ör. "specification.method". */
  field: string;
  message: string;
}

export type ParseResult =
  | { ok: true; items: ReferenceRequirementInput[] }
  | { ok: false; issues: RequirementIssue[] };

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/** HTTP metodu büyük harfe ve boşluksuz biçime getirilir; geçersizse olduğu gibi bırakılır (hata verilir). */
export function normalizeMethod(value: unknown): unknown {
  return typeof value === 'string' ? value.trim().toUpperCase() : value;
}

function validateSpecification(category: RequirementCategory, spec: Record<string, unknown>, push: (f: string, m: string) => void) {
  if (spec.schema_version !== 1) push('specification.schema_version', 'schema_version 1 olmalıdır.');
  if (category === 'ROLE') {
    if (typeof spec.role !== 'string' || !spec.role.trim()) push('specification.role', 'Rol adı zorunludur.');
    return;
  }
  if (category === 'ACCESS_RULE') {
    if (typeof spec.endpoint !== 'string' || !spec.endpoint.trim()) {
      push('specification.endpoint', 'Endpoint yolu zorunludur (ör. /api/orders/).');
    }
    const method = spec.method;
    if (typeof method !== 'string' || !HTTP_METHODS.includes(method as HttpMethod)) {
      push(
        'specification.method',
        `Desteklenmeyen HTTP metodu${typeof method === 'string' && method ? ` "${method}"` : ''}. İzin verilenler: ${HTTP_METHODS.join(', ')}.`,
      );
    }
    const roles = spec.expected_status_by_role;
    if (!isObject(roles) || Object.keys(roles).length === 0) {
      push('specification.expected_status_by_role', 'Rol → beklenen HTTP durum kodu eşlemesi zorunludur.');
    } else {
      for (const [role, code] of Object.entries(roles)) {
        if (!Number.isInteger(code) || (code as number) < 100 || (code as number) > 599) {
          push(`specification.expected_status_by_role.${role}`, 'Durum kodu 100–599 arasında bir tam sayı olmalıdır.');
        }
      }
    }
    return;
  }
  if (typeof spec.setting !== 'string' || !spec.setting.trim()) push('specification.setting', 'Ayar adı zorunludur.');
  if (!('expected_value' in spec)) push('specification.expected_value', 'Beklenen değer zorunludur.');
}

function validateItem(raw: unknown, index: number, issues: RequirementIssue[], projectId: number): ReferenceRequirementInput | null {
  const push = (field: string, message: string) => issues.push({ index, field, message });
  if (!isObject(raw)) {
    push('(kayıt)', 'Her gereksinim bir JSON nesnesi olmalıdır.');
    return null;
  }
  if ('project' in raw && raw.project !== projectId) {
    push('project', 'Proje alanı gönderilmez; gereksinim açık olan projeye eklenir.');
  }
  for (const key of Object.keys(raw)) {
    if (key !== 'project' && !ALLOWED_KEYS.has(key)) push(key, 'Bu alan desteklenmiyor.');
  }
  const code = raw.requirement_code;
  if (typeof code !== 'string' || !CODE_PATTERN.test(code)) {
    push('requirement_code', 'Kod zorunludur; harf/rakamla başlamalı ve yalnızca harf, rakam, ".", "_", "-" içermelidir.');
  }
  const category = raw.category;
  const validCategory = typeof category === 'string' && CATEGORIES.includes(category as RequirementCategory);
  if (!validCategory) push('category', `Kategori ${CATEGORIES.join(', ')} değerlerinden biri olmalıdır.`);
  if (typeof raw.title !== 'string' || !raw.title.trim()) push('title', 'Başlık zorunludur.');
  if (validCategory && category !== 'ROLE' && (typeof raw.expected_result !== 'string' || !raw.expected_result.trim())) {
    push('expected_result', 'ROLE dışındaki kategorilerde beklenen sonuç zorunludur.');
  }
  if (raw.is_active !== undefined && typeof raw.is_active !== 'boolean') push('is_active', 'true veya false olmalıdır.');

  let specification: Record<string, unknown> = {};
  if (!isObject(raw.specification)) {
    push('specification', 'specification bir JSON nesnesi olmalıdır.');
  } else {
    specification = { ...raw.specification };
    if ('method' in specification) specification.method = normalizeMethod(specification.method);
    if (validCategory) validateSpecification(category as RequirementCategory, specification, push);
  }
  if (issues.some((i) => i.index === index)) return null;
  return {
    project: projectId,
    requirement_code: code as string,
    category: category as RequirementCategory,
    source: 'JSON_UPLOAD',
    title: (raw.title as string).trim(),
    description: typeof raw.description === 'string' ? raw.description : '',
    expected_result: typeof raw.expected_result === 'string' ? raw.expected_result : '',
    specification,
    is_active: raw.is_active === undefined ? true : (raw.is_active as boolean),
  };
}

/** JSON metnini ayrıştırır; tek nesne veya nesne dizisi kabul edilir. */
export function parseRequirementJson(text: string, projectId: number): ParseResult {
  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch (error) {
    const detail = error instanceof Error ? error.message : '';
    return { ok: false, issues: [{ index: 1, field: '(JSON)', message: `Geçersiz JSON sözdizimi. ${detail}`.trim() }] };
  }
  const list = Array.isArray(data) ? data : [data];
  if (list.length === 0) return { ok: false, issues: [{ index: 1, field: '(JSON)', message: 'En az bir gereksinim girin.' }] };
  const issues: RequirementIssue[] = [];
  const items = list.map((raw, i) => validateItem(raw, i + 1, issues, projectId));
  if (issues.length > 0) return { ok: false, issues };
  const codes = items.map((item) => item?.requirement_code);
  const duplicate = codes.find((c, i) => codes.indexOf(c) !== i);
  if (duplicate) {
    return { ok: false, issues: [{ index: codes.lastIndexOf(duplicate) + 1, field: 'requirement_code', message: `"${duplicate}" kodu listede birden fazla kez geçiyor.` }] };
  }
  return { ok: true, items: items as ReferenceRequirementInput[] };
}

/** Düzenleme için kaydın JSON gösterimi (yalnızca yazılabilir alanlar). */
export function toEditableJson(item: {
  requirement_code: string;
  category: RequirementCategory;
  title: string;
  description?: string;
  expected_result?: string;
  specification?: unknown;
  is_active?: boolean;
}): string {
  return JSON.stringify(
    {
      requirement_code: item.requirement_code,
      category: item.category,
      title: item.title,
      description: item.description ?? '',
      expected_result: item.expected_result ?? '',
      specification: item.specification ?? {},
      is_active: item.is_active ?? true,
    },
    null,
    2,
  );
}

export const SAMPLE_REQUIREMENT_JSON = JSON.stringify(
  [
    {
      requirement_code: 'ACC-ORNEK-1',
      category: 'ACCESS_RULE',
      title: 'Anonim kullanıcı sipariş listesini göremez',
      expected_result: 'Kimliksiz istek 401 döner.',
      specification: {
        schema_version: 1,
        endpoint: '/api/orders/',
        method: 'GET',
        expected_status_by_role: { anonim: 401, kullanici: 200 },
      },
    },
  ],
  null,
  2,
);
