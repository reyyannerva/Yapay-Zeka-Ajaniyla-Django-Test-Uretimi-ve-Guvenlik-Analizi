// Birim/bileşen testleri için sahte HTTP backend (H5-03 / #41).
//
// Testler gerçek `apiFetch` + servis kodunu çalıştırır; yalnızca `fetch` bu modüldeki bellek içi
// işleyicilere yönlendirilir. Yanıt biçimleri ve durum kodları Django/DRF sözleşmesini (docs/api/) taklit
// eder. Bu bir GERÇEK backend veya PostgreSQL entegrasyon testi DEĞİLDİR; gerçek entegrasyon kanıtı
// e2e/h5-03 altındaki tarayıcı testleri ve backend pytest testleridir.
import type {
  AnalysisRun,
  AnalysisRunDetail,
  Project,
  ReferenceRequirement,
} from '../types';
import { MOCK_FORBIDDEN_PROJECT_ID, mockAnalysisRuns, mockProjectStore, resetMockProjects } from '../lib/api/mock';

export { MOCK_FORBIDDEN_PROJECT_ID };

/** Bu parola "yanlış" sayılır: 1-2. deneme 401, 3. deneme 429 (hesap kilidi). */
export const MOCK_WRONG_PASSWORD = 'yanlis-parola';
/** Şifre sıfırlama onayında bu token geçersiz/süresi dolmuş/kullanılmış sayılır (400 `token`). */
export const MOCK_INVALID_RESET_TOKEN = 'gecersiz-token';
export const FAKE_USER = { id: 1, username: 'ornek-kullanici', email: 'ornek@example.test' };
export const LOCK_SECONDS = 900;

const MAX_ARCHIVE_BYTES = 52_428_800;
const HTTP_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'];
const ACTIVE = ['QUEUED', 'ANALYZING', 'GENERATING', 'VALIDATING', 'EXECUTING', 'SCANNING'];

interface FakeState {
  failedAttempts: number;
  requirements: ReferenceRequirement[];
  nextRequirementId: number;
  nextRunId: number;
  createdRuns: AnalysisRunDetail[];
  calls: { method: string; path: string; body: unknown; headers: Headers }[];
}

const state: FakeState = {
  failedAttempts: 0,
  requirements: [],
  nextRequirementId: 1,
  nextRunId: 100,
  createdRuns: [],
  calls: [],
};

export function resetFakeApi(): void {
  resetMockProjects();
  state.failedAttempts = 0;
  state.requirements = [];
  state.nextRequirementId = 1;
  state.nextRunId = 100;
  state.createdRuns = [];
  state.calls = [];
}

/** Testlerin isteği doğrulayabilmesi için alınan çağrılar. */
export function fakeCalls() {
  return state.calls;
}

export function seedRequirement(partial: Partial<ReferenceRequirement> & { project: number; requirement_code: string }) {
  const now = '2026-03-01T10:00:00Z';
  const item: ReferenceRequirement = {
    id: state.nextRequirementId++,
    category: 'ROLE',
    source: 'FORM',
    title: 'Örnek',
    description: '',
    expected_result: '',
    specification: { schema_version: 1, role: 'kullanici' },
    is_active: true,
    revision: 1,
    http_method: null,
    created_at: now,
    updated_at: now,
    ...partial,
  };
  state.requirements.push(item);
  return item;
}

function json(status: number, body?: unknown, headers: Record<string, string> = {}): Response {
  if (body === undefined) return new Response(null, { status, headers });
  return new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json', ...headers } });
}

const notFound = (model: string) => json(404, { detail: `No ${model} matches the given query.` });

function allRuns(): AnalysisRunDetail[] {
  return [...state.createdRuns, ...mockAnalysisRuns];
}

function toListItem(detail: AnalysisRunDetail): AnalysisRun {
  const { requirements_snapshot: _s, generated_test_count: _g, progress: _p, ...row } = detail;
  return row;
}

function readJson(body: BodyInit | null | undefined): Record<string, unknown> {
  if (typeof body !== 'string') return {};
  try {
    return JSON.parse(body) as Record<string, unknown>;
  } catch {
    return {};
  }
}

function withMethod(item: ReferenceRequirement): ReferenceRequirement {
  const spec = item.specification as { method?: string } | undefined;
  return { ...item, http_method: item.category === 'ACCESS_RULE' ? ((spec?.method ?? null) as ReferenceRequirement['http_method']) : null };
}

function validateRequirement(data: Record<string, unknown>): Record<string, unknown> | null {
  const spec = data.specification as Record<string, unknown> | undefined;
  if (data.category === 'ACCESS_RULE' && (!spec || !HTTP_METHODS.includes(String(spec.method)))) {
    return { specification: { method: [`"${String(spec?.method)}" geçerli bir seçim değil.`] } };
  }
  if (!mockProjectStore.projects.some((p) => p.id === data.project)) {
    return { project: ['Geçersiz pk "' + String(data.project) + '" - obje mevcut değil.'] };
  }
  return null;
}

async function handle(method: string, path: string, init: RequestInit | undefined): Promise<Response> {
  const body = init?.body;
  const data = readJson(body as BodyInit | null);
  let m: RegExpMatchArray | null;

  // --- kimlik doğrulama ---
  if (path === '/api/auth/login/' && method === 'POST') {
    if (state.failedAttempts >= 3) {
      return json(429, { detail: 'Çok fazla başarısız giriş denemesi.', code: 'account_locked', locked_until: '2026-01-01T12:15:00+03:00', retry_after_seconds: LOCK_SECONDS }, { 'Retry-After': String(LOCK_SECONDS) });
    }
    if (data.password === MOCK_WRONG_PASSWORD) {
      state.failedAttempts += 1;
      if (state.failedAttempts >= 3) {
        return json(429, { detail: 'Çok fazla başarısız giriş denemesi.', code: 'account_locked', locked_until: '2026-01-01T12:15:00+03:00', retry_after_seconds: LOCK_SECONDS }, { 'Retry-After': String(LOCK_SECONDS) });
      }
      return json(401, { detail: 'Verilen kimlik bilgileriyle aktif bir hesap bulunamadı' });
    }
    state.failedAttempts = 0;
    return json(200, { access: 'test-access', refresh: 'test-refresh' });
  }
  if (path === '/api/auth/refresh/' && method === 'POST') return json(200, { access: 'test-access-2', refresh: 'test-refresh-2' });
  if (path === '/api/auth/logout/' && method === 'POST') return json(205);
  if (path === '/api/auth/me/' && method === 'GET') return json(200, FAKE_USER);
  if (path === '/api/auth/password-reset/' && method === 'POST') {
    if (typeof data.email !== 'string' || !data.email.includes('@')) return json(400, { email: ['Geçerli bir e-posta adresi girin.'] });
    return json(200, { detail: 'E-posta kayıtlıysa şifre sıfırlama bağlantısı gönderildi.' });
  }
  if (path === '/api/auth/password-reset/confirm/' && method === 'POST') {
    if (data.token === MOCK_INVALID_RESET_TOKEN) return json(400, { token: ['Bağlantı geçersiz veya süresi dolmuş.'] });
    if (typeof data.new_password !== 'string' || data.new_password.length < 8) {
      return json(400, { new_password: ['Bu parola çok kısa. En az 8 karakter olmalı.'] });
    }
    return json(200, { detail: 'Parola güncellendi.' });
  }

  // --- projeler ---
  if (path.startsWith('/api/projects/') && path.split('?')[0] === '/api/projects/' && method === 'GET') {
    const params = new URLSearchParams(path.split('?')[1] ?? '');
    const pageSize = Math.min(Number(params.get('page_size') ?? 20), 100);
    const page = Number(params.get('page') ?? 1);
    const sorted = [...mockProjectStore.projects].sort((a, b) => b.created_at.localeCompare(a.created_at));
    const start = (page - 1) * pageSize;
    return json(200, {
      count: sorted.length,
      next: start + pageSize < sorted.length ? `?page=${page + 1}` : null,
      previous: page > 1 ? `?page=${page - 1}` : null,
      results: sorted.slice(start, start + pageSize),
    });
  }
  if (path === '/api/projects/' && method === 'POST') {
    if (!(body instanceof FormData)) return json(415, { detail: 'Proje oluşturma multipart/form-data ile yapılmalıdır.' });
    const archive = body.get('archive');
    const name = String(body.get('name') ?? '');
    if (!(archive instanceof File)) return json(400, { archive: ['Dosya gönderilmedi.'] });
    if (archive.size > MAX_ARCHIVE_BYTES) return json(413, { detail: `Yüklenen dosya en fazla ${MAX_ARCHIVE_BYTES} bayt olabilir.` });
    if (!archive.name.toLowerCase().endsWith('.zip')) {
      return json(400, { archive: [{ code: 'UNSUPPORTED_TYPE', detail: 'Yalnızca .zip arşivleri kabul edilir.' }] });
    }
    if (mockProjectStore.projects.some((p) => p.name === name)) return json(400, { name: ['Bu adla kayıtlı bir projeniz zaten var.'] });
    const now = new Date().toISOString();
    const project: Project = {
      id: mockProjectStore.nextId++,
      name,
      description: String(body.get('description') ?? ''),
      source_type: 'ARCHIVE',
      validation_status: 'VALID',
      archive: { original_name: archive.name, size_bytes: archive.size, sha256: '0'.repeat(64), uploaded_at: now },
      validation_report: {},
      analysis_run_count: 0,
      created_at: now,
      updated_at: now,
    };
    mockProjectStore.projects.push(project);
    return json(201, project);
  }
  if ((m = path.match(/^\/api\/projects\/(\d+)\/$/))) {
    const id = Number(m[1]);
    if (id === MOCK_FORBIDDEN_PROJECT_ID) return json(403, { detail: 'Bu işlemi yapmak için izniniz yok.' });
    const project = mockProjectStore.projects.find((p) => p.id === id);
    if (!project) return notFound('Project');
    if (method === 'GET') return json(200, project);
    if (method === 'PATCH' || method === 'PUT') {
      const extra = Object.keys(data).filter((k) => !['name', 'description'].includes(k));
      if (extra.length) return json(400, Object.fromEntries(extra.map((k) => [k, ['Bu alan istemci tarafından gönderilemez veya değiştirilemez.']])));
      if (typeof data.name === 'string' && mockProjectStore.projects.some((p) => p.name === data.name && p.id !== id)) {
        return json(400, { name: ['Bu adla kayıtlı bir projeniz zaten var.'] });
      }
      if (typeof data.name === 'string') project.name = data.name;
      if (typeof data.description === 'string') project.description = data.description;
      project.updated_at = new Date().toISOString();
      return json(200, project);
    }
    if (method === 'DELETE') {
      if (allRuns().some((r) => r.project === id && ACTIVE.includes(r.status))) {
        return json(409, { detail: 'Projenin devam eden bir analizi var; analiz bitmeden proje silinemez.' });
      }
      mockProjectStore.projects = mockProjectStore.projects.filter((p) => p.id !== id);
      return json(204);
    }
  }

  // --- analiz çalıştırmaları ---
  if (path === '/api/analysis-runs/' && method === 'GET') return json(200, allRuns().map(toListItem));
  if (path === '/api/analysis-runs/' && method === 'POST') {
    const project = mockProjectStore.projects.find((p) => p.id === data.project);
    if (!project) return json(400, { project: [`Geçersiz pk "${String(data.project)}" - obje mevcut değil.`] });
    if (data.method !== 'RULE_BASED' && (!data.llm_provider || !data.llm_model)) {
      return json(400, { llm_model: ['LLM yöntemlerinde llm_provider ve llm_model zorunludur.'] });
    }
    const now = new Date().toISOString();
    const run: AnalysisRunDetail = {
      id: state.nextRunId++,
      project: project.id,
      status: 'QUEUED',
      method: data.method as AnalysisRunDetail['method'],
      llm_provider: (data.llm_provider ?? null) as AnalysisRunDetail['llm_provider'],
      llm_model: (data.llm_model ?? null) as string | null,
      fallback_enabled: Boolean(data.fallback_enabled ?? true),
      celery_task_id: null,
      coverage_percent: null,
      error_code: '',
      error_message: '',
      created_at: now,
      started_at: null,
      finished_at: null,
      updated_at: now,
      requirements_snapshot: [],
      generated_test_count: 0,
      progress: { total: 0, completed: 0, running: 0, pending: 0, by_status: {}, completed_duration_ms_total: 0, completed_with_duration: 0, run_started_at: null, percent: null },
    };
    state.createdRuns.unshift(run);
    return json(201, run);
  }
  if ((m = path.match(/^\/api\/analysis-runs\/(\d+)\/$/)) && method === 'GET') {
    const run = allRuns().find((r) => r.id === Number(m![1]));
    return run ? json(200, run) : notFound('AnalysisRun');
  }

  // --- referans gereksinimler ---
  if (path === '/api/reference-requirements/' && method === 'GET') return json(200, state.requirements.map(withMethod));
  if (path === '/api/reference-requirements/' && method === 'POST') {
    const error = validateRequirement(data);
    if (error) return json(400, error);
    if (state.requirements.some((r) => r.project === data.project && r.requirement_code === data.requirement_code)) {
      return json(400, { non_field_errors: ['project, requirement_code alanları benzersiz bir küme oluşturmalıdır.'] });
    }
    const item = seedRequirement(data as unknown as ReferenceRequirement);
    return json(201, withMethod(item));
  }
  if ((m = path.match(/^\/api\/reference-requirements\/(\d+)\/$/))) {
    const item = state.requirements.find((r) => r.id === Number(m![1]));
    if (!item) return notFound('ReferenceRequirement');
    if (method === 'GET') return json(200, withMethod(item));
    if (method === 'PUT' || method === 'PATCH') {
      const merged = { ...item, ...data } as ReferenceRequirement;
      const error = validateRequirement(merged as unknown as Record<string, unknown>);
      if (error) return json(400, error);
      Object.assign(item, data, { revision: item.revision + 1 });
      return json(200, withMethod(item));
    }
    if (method === 'DELETE') {
      state.requirements = state.requirements.filter((r) => r.id !== item.id);
      return json(204);
    }
  }
  return json(404, { detail: 'Bulunamadı.' });
}

/** `fetch`'i sahte backend'e yönlendirir. */
export async function fakeFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const url = new URL(typeof input === 'string' ? input : input instanceof URL ? input.href : input.url);
  const method = (init?.method ?? 'GET').toUpperCase();
  const path = url.pathname + url.search;
  state.calls.push({ method, path, body: init?.body, headers: new Headers(init?.headers) });
  if (init?.signal?.aborted) throw new DOMException('Aborted', 'AbortError');
  return handle(method, path, init);
}
