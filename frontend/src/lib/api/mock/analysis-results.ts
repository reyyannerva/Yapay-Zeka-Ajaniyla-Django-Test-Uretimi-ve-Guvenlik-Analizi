// AÇIKÇA ÖRNEK (DEMO) VERİ — gerçek bir AST analizi, test üretimi, sandbox yürütmesi veya güvenlik
// taraması sonucu değildir. Kayıtlar mock/analysis-runs.ts'teki analizlerle tutarlıdır:
//  #1 FAILED (test üretilmeden; endpoint yok)   #2 EXECUTING (canlı akış)   #3 QUEUED (henüz veri yok)
//  #4 COMPLETED hibrit (fallback, 5 HTTP metodu, tüm uç durumlar, üç bulgu sınıfı, değerlendirme verisi)
//  #5 COMPLETED kural tabanlı (bulgu yok, değerlendirme verisi yok)
//  #6 FAILED kısmi sonuç (model bilgisi yok, rapor hazırlama hatası senaryosu)
import type {
  EndpointAnalysis,
  EvaluationCounts,
  ExecutionSnapshot,
  GeneratedTest,
  GenerationMetadata,
  HttpMethod,
  SecurityFinding,
  TestExecutionResult,
  TestExecutionStatus,
  TestGenerationMethod,
} from '../../../types';

// ---------------------------------------------------------------- yardımcılar
function ep(
  id: number,
  run: number,
  http_method: HttpMethod,
  path: string,
  view_name: string,
  auth_type: string,
  permission_classes: string[],
  unsupported: EndpointAnalysis['unsupported_reason'] = null,
): EndpointAnalysis {
  return {
    id,
    analysis_run: run,
    path,
    http_method,
    view_name,
    auth_type,
    permission_classes,
    is_supported: unsupported === null,
    unsupported_reason: unsupported,
  };
}

const CLIENT_CALL: Record<HttpMethod, string> = {
  GET: 'get',
  POST: 'post',
  PUT: 'put',
  PATCH: 'patch',
  DELETE: 'delete',
};

function pytestSource(name: string, method: HttpMethod, url: string, role: string, expected: number): string {
  const call = CLIENT_CALL[method];
  const body = method === 'GET' || method === 'DELETE' ? '' : ', {"quantity": 1}, format="json"';
  const auth =
    role === 'anonim'
      ? '    # anonim istek: kimlik doğrulaması yapılmaz'
      : `    api_client.force_authenticate(user=users["${role}"])`;
  return [
    'import pytest',
    '',
    'pytestmark = pytest.mark.django_db',
    '',
    '',
    `def ${name}(api_client, users, seeded_db):`,
    auth,
    `    response = api_client.${call}("${url}"${body})`,
    `    assert response.status_code == ${expected}`,
    '',
  ].join('\n');
}

let shaSeed = 0;
function fakeSha(): string {
  shaSeed += 1;
  // Örnek veri: gerçek bir dosya özeti değildir.
  return `demo${String(shaSeed).padStart(4, '0')}`.padEnd(64, '0');
}

interface TestSpec {
  id: number;
  run: number;
  endpoint: EndpointAnalysis | null;
  name: string;
  method: TestGenerationMethod;
  role: string;
  expected: number | null;
  security: boolean;
  url: string;
  requirement?: string;
  meta?: GenerationMetadata;
  validation?: GeneratedTest['validation_status'];
  validationErrors?: string[];
  repairs?: number;
  source?: string;
}

function test(spec: TestSpec): GeneratedTest {
  const httpMethod = spec.endpoint?.http_method ?? 'GET';
  return {
    id: spec.id,
    analysis_run: spec.run,
    endpoint: spec.endpoint?.id ?? null,
    test_module: `tests/test_${spec.run}_generated.py`,
    test_name: spec.name,
    generation_method: spec.method,
    requirement_code: spec.requirement ?? '',
    role: spec.role,
    expected_status: spec.expected,
    is_security_test: spec.security,
    source_code:
      spec.source ?? pytestSource(spec.name, httpMethod, spec.url, spec.role, spec.expected ?? 200),
    code_sha256: fakeSha(),
    validation_status: spec.validation ?? 'VALID',
    validation_errors: spec.validationErrors ?? [],
    repair_count: spec.repairs ?? 0,
    generation_metadata: spec.meta ?? {},
  };
}

function result(
  id: number,
  generated_test: number,
  status: TestExecutionStatus,
  extra: Partial<TestExecutionResult> = {},
): TestExecutionResult {
  return {
    id,
    generated_test,
    attempt_number: 1,
    status,
    observed_status: null,
    error_type: null,
    error_origin: null,
    started_at: null,
    finished_at: null,
    duration_ms: null,
    output_excerpt: '',
    error_summary: '',
    ...extra,
  };
}

const GROQ: GenerationMetadata = {
  requested_provider: 'GROQ',
  requested_model: 'ornek-model',
  provider: 'GROQ',
  model: 'ornek-model',
  fallback_used: false,
  prompt_version: 'pytest_v1',
};
const GROQ_TO_GEMINI: GenerationMetadata = {
  requested_provider: 'GROQ',
  requested_model: 'ornek-model',
  provider: 'GEMINI',
  model: 'ornek-yedek-model',
  fallback_used: true,
  fallback_reason: 'Birincil sağlayıcı kota sınırına ulaştı (HTTP 429)',
  prompt_version: 'pytest_v1',
};

// ---------------------------------------------------------------- #2 EXECUTING (canlı)
const E2 = [
  ep(201, 2, 'GET', '/api/notes/', 'NoteListCreateView', 'Token', ['IsAuthenticated']),
  ep(202, 2, 'POST', '/api/notes/', 'NoteListCreateView', 'Token', ['IsAuthenticated']),
  ep(203, 2, 'PUT', '/api/notes/<int:pk>/', 'NoteDetailView', 'Token', ['IsAuthenticated']),
  ep(204, 2, 'PATCH', '/api/notes/<int:pk>/', 'NoteDetailView', 'Token', ['IsAuthenticated']),
  ep(205, 2, 'DELETE', '/api/notes/<int:pk>/', 'NoteDetailView', 'Token', ['IsAuthenticated']),
];
const T2: GeneratedTest[] = [
  test({ id: 2001, run: 2, endpoint: E2[0]!, name: 'test_note_list_requires_auth', method: 'RULE_BASED', role: 'anonim', expected: 401, security: true, url: '/api/notes/' }),
  test({ id: 2002, run: 2, endpoint: E2[0]!, name: 'test_note_list_owner_ok', method: 'RULE_BASED', role: 'sahip', expected: 200, security: false, url: '/api/notes/' }),
  test({ id: 2003, run: 2, endpoint: E2[1]!, name: 'test_note_create_owner_created', method: 'LLM', role: 'sahip', expected: 201, security: false, url: '/api/notes/', meta: GROQ }),
  test({ id: 2004, run: 2, endpoint: E2[2]!, name: 'test_note_update_other_user_forbidden', method: 'LLM', role: 'kullanici', expected: 403, security: true, url: '/api/notes/7/', meta: GROQ }),
  test({ id: 2005, run: 2, endpoint: E2[2]!, name: 'test_note_update_owner_ok', method: 'RULE_BASED', role: 'sahip', expected: 200, security: false, url: '/api/notes/7/' }),
  test({ id: 2006, run: 2, endpoint: E2[3]!, name: 'test_note_partial_update_other_user_forbidden', method: 'LLM', role: 'kullanici', expected: 403, security: true, url: '/api/notes/7/', meta: GROQ_TO_GEMINI }),
  test({ id: 2007, run: 2, endpoint: E2[3]!, name: 'test_note_partial_update_invalid_title', method: 'LLM', role: 'sahip', expected: 400, security: false, url: '/api/notes/7/', meta: GROQ_TO_GEMINI }),
  test({ id: 2008, run: 2, endpoint: E2[4]!, name: 'test_note_delete_other_user_forbidden', method: 'RULE_BASED', role: 'kullanici', expected: 403, security: true, url: '/api/notes/7/' }),
  test({ id: 2009, run: 2, endpoint: E2[4]!, name: 'test_note_delete_owner_no_content', method: 'LLM', role: 'sahip', expected: 204, security: false, url: '/api/notes/7/', meta: GROQ }),
  test({ id: 2010, run: 2, endpoint: E2[4]!, name: 'test_note_delete_anonymous_unauthorized', method: 'RULE_BASED', role: 'anonim', expected: 401, security: true, url: '/api/notes/7/' }),
];

/** Akışın başlangıcı: mock/analysis-runs.ts #2 progress ile aynı (3 PASS, 1 FAIL, 1 RUNNING, 5 PENDING). */
function run2Initial(): TestExecutionResult[] {
  return [
    result(20001, 2001, 'PASS', { observed_status: 401, duration_ms: 100, output_excerpt: '1 passed in 0.10s' }),
    result(20002, 2002, 'PASS', { observed_status: 200, duration_ms: 100, output_excerpt: '1 passed in 0.10s' }),
    result(20003, 2003, 'PASS', { observed_status: 201, duration_ms: 100, output_excerpt: '1 passed in 0.10s' }),
    result(20004, 2004, 'FAIL', {
      observed_status: 200,
      duration_ms: 100,
      error_summary: 'AssertionError: assert 200 == 403',
      output_excerpt: '>       assert response.status_code == 403\nE       AssertionError: assert 200 == 403\n1 failed in 0.10s',
    }),
    result(20005, 2005, 'RUNNING'),
    result(20006, 2006, 'PENDING'),
    result(20007, 2007, 'PENDING'),
    result(20008, 2008, 'PENDING'),
    result(20009, 2009, 'PENDING'),
    result(20010, 2010, 'PENDING'),
  ];
}

/** Canlı akışta her testin ulaşacağı sonuç (deterministik). */
const RUN2_FINAL: Record<number, Partial<TestExecutionResult> & { status: TestExecutionStatus }> = {
  2005: { status: 'PASS', observed_status: 200, duration_ms: 180, output_excerpt: '1 passed in 0.18s' },
  2006: {
    status: 'FAIL',
    observed_status: 200,
    duration_ms: 210,
    error_summary: 'AssertionError: assert 200 == 403',
    output_excerpt: '>       assert response.status_code == 403\nE       AssertionError: assert 200 == 403\n1 failed in 0.21s',
  },
  2007: {
    status: 'ERROR',
    duration_ms: 40,
    error_type: 'FIXTURE',
    error_origin: 'TEST_CODE',
    error_summary: "fixture 'note_factory' not found",
    output_excerpt: "E       fixture 'note_factory' not found\n1 error in 0.04s",
  },
  2008: {
    status: 'TIMEOUT',
    duration_ms: 30_000,
    error_type: 'TIMEOUT',
    error_origin: 'INFRASTRUCTURE',
    error_summary: '30 sn süre sınırı aşıldı',
    output_excerpt: 'Timeout: test 30.00 sn içinde tamamlanmadı',
  },
  2009: { status: 'PASS', observed_status: 204, duration_ms: 150, output_excerpt: '1 passed in 0.15s' },
  2010: { status: 'PASS', observed_status: 401, duration_ms: 120, output_excerpt: '1 passed in 0.12s' },
};

// ---------------------------------------------------------------- #4 COMPLETED hibrit
const E4 = [
  ep(401, 4, 'GET', '/api/orders/', 'OrderListCreateView', 'Token', ['IsAuthenticated']),
  ep(402, 4, 'POST', '/api/orders/', 'OrderListCreateView', 'Token', ['IsAuthenticated']),
  ep(403, 4, 'GET', '/api/orders/<int:pk>/', 'OrderDetailView', 'Token', ['IsAuthenticated']),
  ep(404, 4, 'PUT', '/api/orders/<int:pk>/', 'OrderDetailView', 'Token', ['IsAuthenticated']),
  ep(405, 4, 'PATCH', '/api/orders/<int:pk>/', 'OrderDetailView', 'Token', ['IsAuthenticated']),
  ep(406, 4, 'DELETE', '/api/orders/<int:pk>/', 'OrderDetailView', 'Token', ['IsAuthenticated']),
  ep(407, 4, 'GET', '/api/users/', 'UserListView', 'Token', ['IsAdminUser']),
  ep(408, 4, 'GET', '/api/products/', 'ProductListView', '', ['AllowAny']),
  ep(409, 4, 'GET', '/api/reports/<str:kind>/', 'ReportView', 'Token', ['HasReportAccess'], 'CUSTOM_PERMISSION'),
  ep(410, 4, 'GET', '^api/v(?P<version>\\d)/export/$', 'ExportView', 'Token', ['IsAuthenticated'], 'DYNAMIC_ROUTE'),
];
const LONG_NAME =
  'test_order_detail_other_user_forbidden_even_with_valid_token_and_existing_order_identifier';
const T4: GeneratedTest[] = [
  test({ id: 4001, run: 4, endpoint: E4[0]!, name: 'test_order_list_requires_auth', method: 'RULE_BASED', role: 'anonim', expected: 401, security: true, url: '/api/orders/', requirement: 'ACC-ORDERS-LIST' }),
  test({ id: 4002, run: 4, endpoint: E4[0]!, name: 'test_order_list_owner_ok', method: 'LLM', role: 'sahip', expected: 200, security: false, url: '/api/orders/', meta: GROQ }),
  test({ id: 4003, run: 4, endpoint: E4[1]!, name: 'test_order_create_rejects_negative_qty', method: 'LLM', role: 'sahip', expected: 400, security: false, url: '/api/orders/', meta: GROQ, repairs: 1 }),
  test({ id: 4004, run: 4, endpoint: E4[2]!, name: LONG_NAME, method: 'LLM', role: 'kullanici', expected: 403, security: true, url: '/api/orders/1042/', requirement: 'ACC-ORDERS-DETAIL', meta: GROQ_TO_GEMINI }),
  test({ id: 4005, run: 4, endpoint: E4[2]!, name: 'test_order_detail_owner_can_view', method: 'RULE_BASED', role: 'sahip', expected: 200, security: false, url: '/api/orders/1042/' }),
  test({ id: 4006, run: 4, endpoint: E4[3]!, name: 'test_order_update_owner_ok', method: 'LLM', role: 'sahip', expected: 200, security: false, url: '/api/orders/1042/', meta: GROQ_TO_GEMINI }),
  test({ id: 4007, run: 4, endpoint: E4[4]!, name: 'test_order_partial_update_anonymous_unauthorized', method: 'RULE_BASED', role: 'anonim', expected: 401, security: true, url: '/api/orders/1042/' }),
  test({ id: 4008, run: 4, endpoint: E4[5]!, name: 'test_order_delete_other_user_forbidden', method: 'RULE_BASED', role: 'kullanici', expected: 403, security: true, url: '/api/orders/1042/', requirement: 'ACC-ORDERS-DELETE' }),
  test({ id: 4009, run: 4, endpoint: E4[5]!, name: 'test_order_delete_owner_no_content', method: 'LLM', role: 'sahip', expected: 204, security: false, url: '/api/orders/1042/', meta: GROQ }),
  test({ id: 4010, run: 4, endpoint: E4[6]!, name: 'test_user_list_requires_admin', method: 'RULE_BASED', role: 'kullanici', expected: 403, security: true, url: '/api/users/' }),
  test({ id: 4011, run: 4, endpoint: E4[6]!, name: 'test_user_list_admin_ok', method: 'LLM', role: 'yonetici', expected: 200, security: false, url: '/api/users/', meta: GROQ }),
  test({ id: 4012, run: 4, endpoint: E4[7]!, name: 'test_product_list_public', method: 'LLM', role: 'anonim', expected: 200, security: false, url: '/api/products/', meta: GROQ_TO_GEMINI }),
  test({
    id: 4013,
    run: 4,
    endpoint: E4[1]!,
    name: 'test_order_create_admin_bulk',
    method: 'LLM',
    role: 'yonetici',
    expected: 201,
    security: false,
    url: '/api/orders/',
    meta: GROQ,
    validation: 'INVALID_SYNTAX',
    validationErrors: ['SyntaxError: unexpected EOF while parsing (satır 9)'],
    repairs: 1,
    source: 'import pytest\n\n\ndef test_order_create_admin_bulk(api_client, users):\n    api_client.force_authenticate(user=users["yonetici"])\n    response = api_client.post("/api/orders/bulk/", [\n',
  }),
];
const LONG_OUTPUT = Array.from(
  { length: 40 },
  (_, i) => `DEBUG istek ${String(i + 1).padStart(2, '0')}: GET /api/orders/1042/ HTTP/1.1 → 200 OK (uzun çıktı satırı, kaydırılabilir alanda gösterilir)`,
).join('\n');
const R4: TestExecutionResult[] = [
  result(40001, 4001, 'PASS', { observed_status: 401, duration_ms: 290, output_excerpt: '1 passed in 0.29s' }),
  result(40002, 4002, 'PASS', { observed_status: 200, duration_ms: 360, output_excerpt: '1 passed in 0.36s' }),
  result(40003, 4003, 'FAIL', {
    observed_status: 201,
    duration_ms: 440,
    error_summary: 'AssertionError: assert 201 == 400',
    output_excerpt: 'tests/test_4_generated.py:9\n>       assert response.status_code == 400\nE       AssertionError: assert 201 == 400',
  }),
  result(40004, 4004, 'FAIL', {
    observed_status: 200,
    duration_ms: 410,
    error_summary: 'AssertionError: assert 200 == 403',
    output_excerpt: `tests/test_4_generated.py:9\n>       assert response.status_code == 403\nE       AssertionError: assert 200 == 403\n${LONG_OUTPUT}`,
  }),
  result(40005, 4005, 'PASS', { observed_status: 200, duration_ms: 360, output_excerpt: '1 passed in 0.36s' }),
  result(40006, 4006, 'PASS', { observed_status: 200, duration_ms: 520, output_excerpt: '1 passed in 0.52s' }),
  result(40007, 4007, 'PASS', { observed_status: 401, duration_ms: 310, output_excerpt: '1 passed in 0.31s' }),
  result(40008, 4008, 'FAIL', {
    observed_status: 204,
    duration_ms: 380,
    error_summary: 'AssertionError: assert 204 == 403',
    output_excerpt: '>       assert response.status_code == 403\nE       AssertionError: assert 204 == 403',
  }),
  result(40009, 4009, 'PASS', { observed_status: 204, duration_ms: 330, output_excerpt: '1 passed in 0.33s' }),
  result(40010, 4010, 'TIMEOUT', {
    duration_ms: 30_000,
    error_type: 'TIMEOUT',
    error_origin: 'INFRASTRUCTURE',
    error_summary: '30 sn süre sınırı aşıldı',
    output_excerpt: 'Timeout: test 30.00 sn içinde tamamlanmadı',
  }),
  result(40011, 4011, 'ERROR', {
    duration_ms: 20,
    error_type: 'IMPORT',
    error_origin: 'TEST_CODE',
    error_summary: "ImportError: cannot import name 'AdminFactory'",
    output_excerpt: "E   ImportError: cannot import name 'AdminFactory' from 'tests.factories'",
  }),
  result(40012, 4012, 'PASS', { observed_status: 200, duration_ms: 3_440, output_excerpt: '1 passed in 3.44s' }),
  result(40013, 4013, 'NOT_RUN', { error_summary: 'Sözdizimi doğrulamasından geçmediği için çalıştırılmadı' }),
];
const F4: SecurityFinding[] = [
  {
    id: 41,
    analysis_run: 4,
    test_execution: 40004,
    endpoint: 403,
    source: 'AUTH_TEST',
    rule_id: 'ACC-ORDERS-DETAIL',
    severity: 'HIGH',
    classification: 'VERIFIED',
    title: 'Başka kullanıcının siparişi görüntülenebiliyor',
    description: 'Referans kurala göre kullanıcı rolü başkasına ait siparişe 403 almalı; çalışan sistem 200 döndürdü.',
    file_path: 'orders/views.py',
    line_number: 28,
    evidence_excerpt: 'GET /api/orders/1042/ (kullanici) → HTTP 200; beklenen 403\n{"id": 1042, "user": 7, "total": "349.90"}',
    recommendation_key: 'OBJECT_LEVEL_AUTHZ',
  },
  {
    id: 42,
    analysis_run: 4,
    test_execution: 40008,
    endpoint: 406,
    source: 'AUTH_TEST',
    rule_id: 'ACC-ORDERS-DELETE',
    severity: 'HIGH',
    classification: 'VERIFIED',
    title: 'Başka kullanıcının siparişi silinebiliyor',
    description: 'Kullanıcı rolü başkasına ait siparişi silebildi (204); beklenen 403.',
    file_path: 'orders/views.py',
    line_number: 28,
    evidence_excerpt: 'DELETE /api/orders/1042/ (kullanici) → HTTP 204; beklenen 403',
    recommendation_key: 'OBJECT_LEVEL_AUTHZ',
  },
  {
    id: 43,
    analysis_run: 4,
    test_execution: null,
    endpoint: null,
    source: 'CHECK_DEPLOY',
    rule_id: 'security.W018',
    severity: 'MEDIUM',
    classification: 'VERIFIED',
    title: 'Canlı ortam ayarında DEBUG açık',
    description: 'manage.py check --deploy, DEBUG=True olduğunu bildirdi.',
    file_path: 'siparis/settings.py',
    line_number: 12,
    evidence_excerpt: '?: (security.W018) You should not have DEBUG set to True in deployment.',
    recommendation_key: 'DEBUG_DISABLED',
  },
  {
    id: 44,
    analysis_run: 4,
    test_execution: null,
    endpoint: null,
    source: 'BANDIT',
    rule_id: 'B602',
    severity: 'HIGH',
    classification: 'POSSIBLE',
    title: 'Kabuk üzerinden komut çalıştırılıyor',
    description: 'Yalnızca statik analiz kanıtı vardır; çalışan sistemde doğrulanmadı.',
    file_path: 'utils/export.py',
    line_number: 42,
    evidence_excerpt: 'subprocess.call(cmd, shell=True)',
    recommendation_key: 'SUBPROCESS_NO_SHELL',
  },
  {
    id: 45,
    analysis_run: 4,
    test_execution: null,
    endpoint: null,
    source: 'BANDIT',
    rule_id: 'B105',
    severity: 'LOW',
    classification: 'POSSIBLE',
    title: 'Kaynak kodda sabit parola benzeri değer',
    description: 'Statik analiz uyarısı; değerin gerçek bir parola olup olmadığı belirlenemedi.',
    file_path: 'siparis/settings.py',
    line_number: 23,
    evidence_excerpt: 'EMAIL_HOST_PASSWORD = "********"',
    recommendation_key: null,
  },
  {
    id: 46,
    analysis_run: 4,
    test_execution: 40010,
    endpoint: 407,
    source: 'AUTH_TEST',
    rule_id: 'ACC-USERS-LIST',
    severity: 'UNKNOWN',
    classification: 'UNCERTAIN',
    title: 'Kullanıcı listesinin yetki kontrolü sonuçlanamadı',
    description: 'Yetki testi TIMEOUT verdi; erişim kuralı doğrulanamadı. Elle inceleme veya testin yeniden çalıştırılması gerekir.',
    file_path: '',
    line_number: null,
    evidence_excerpt: '',
    recommendation_key: null,
  },
];

// ---------------------------------------------------------------- #5 COMPLETED kural tabanlı, bulgu yok
const E5 = [
  ep(501, 5, 'GET', '/api/posts/', 'PostViewSet', 'Session', ['IsAuthenticatedOrReadOnly']),
  ep(502, 5, 'POST', '/api/posts/', 'PostViewSet', 'Session', ['IsAuthenticatedOrReadOnly']),
];
const T5: GeneratedTest[] = [
  test({ id: 5001, run: 5, endpoint: E5[0]!, name: 'test_post_list_public', method: 'RULE_BASED', role: 'anonim', expected: 200, security: false, url: '/api/posts/' }),
  test({ id: 5002, run: 5, endpoint: E5[1]!, name: 'test_post_create_requires_auth', method: 'RULE_BASED', role: 'anonim', expected: 403, security: true, url: '/api/posts/' }),
  test({ id: 5003, run: 5, endpoint: E5[1]!, name: 'test_post_create_user_created', method: 'RULE_BASED', role: 'kullanici', expected: 201, security: false, url: '/api/posts/' }),
  test({ id: 5004, run: 5, endpoint: E5[0]!, name: 'test_post_list_user_ok', method: 'RULE_BASED', role: 'kullanici', expected: 200, security: false, url: '/api/posts/' }),
];
const R5: TestExecutionResult[] = [
  result(50001, 5001, 'PASS', { observed_status: 200, duration_ms: 300, output_excerpt: '1 passed in 0.30s' }),
  result(50002, 5002, 'PASS', { observed_status: 403, duration_ms: 300, output_excerpt: '1 passed in 0.30s' }),
  result(50003, 5003, 'PASS', { observed_status: 201, duration_ms: 300, output_excerpt: '1 passed in 0.30s' }),
  result(50004, 5004, 'PASS', { observed_status: 200, duration_ms: 300, output_excerpt: '' }),
];

// ---------------------------------------------------------------- #6 FAILED, kısmi sonuç
const E6 = [
  ep(601, 6, 'GET', '/api/invoices/', 'InvoiceListView', 'Token', ['IsAuthenticated']),
  ep(602, 6, 'DELETE', '/api/invoices/<int:pk>/', 'InvoiceDetailView', 'Token', []),
];
const T6: GeneratedTest[] = [
  test({ id: 6001, run: 6, endpoint: E6[0]!, name: 'test_invoice_list_requires_auth', method: 'LLM', role: 'anonim', expected: 401, security: true, url: '/api/invoices/' }),
  test({ id: 6002, run: 6, endpoint: E6[1]!, name: 'test_invoice_delete_other_user_forbidden', method: 'LLM', role: 'kullanici', expected: 403, security: true, url: '/api/invoices/3/' }),
  test({ id: 6003, run: 6, endpoint: E6[1]!, name: 'test_invoice_delete_owner_no_content', method: 'LLM', role: 'sahip', expected: 204, security: false, url: '/api/invoices/3/' }),
  test({ id: 6004, run: 6, endpoint: E6[0]!, name: 'test_invoice_list_owner_ok', method: 'LLM', role: 'sahip', expected: 200, security: false, url: '/api/invoices/' }),
];
const R6: TestExecutionResult[] = [
  result(60001, 6001, 'PASS', { observed_status: 401, duration_ms: 400, output_excerpt: '1 passed in 0.40s' }),
  result(60002, 6002, 'FAIL', {
    observed_status: 204,
    duration_ms: 420,
    error_summary: 'AssertionError: assert 204 == 403',
    output_excerpt: '>       assert response.status_code == 403\nE       AssertionError: assert 204 == 403',
  }),
  result(60003, 6003, 'NOT_RUN', { error_summary: 'Sandbox durduğu için çalıştırılmadı' }),
  result(60004, 6004, 'NOT_RUN', { error_summary: 'Sandbox durduğu için çalıştırılmadı' }),
];
const F6: SecurityFinding[] = [
  {
    id: 61,
    analysis_run: 6,
    test_execution: 60002,
    endpoint: 602,
    source: 'AUTH_TEST',
    rule_id: 'ACC-INVOICES-DELETE',
    severity: 'HIGH',
    classification: 'VERIFIED',
    title: 'Başka kullanıcının faturası silinebiliyor',
    description: 'Analiz yarıda kaldı; bu bulgu tamamlanan testlerden gelir (kısmi sonuç).',
    file_path: 'billing/views.py',
    line_number: 51,
    evidence_excerpt: 'DELETE /api/invoices/3/ (kullanici) → HTTP 204; beklenen 403',
    recommendation_key: 'OBJECT_LEVEL_AUTHZ',
  },
];

// ---------------------------------------------------------------- dışa açık veri kümesi
export interface RunResults {
  endpoints: EndpointAnalysis[];
  tests: GeneratedTest[];
  /** Canlı olmayan analizlerde son sonuçlar; #2'de akışın başlangıcı. */
  results: () => TestExecutionResult[];
  findings: SecurityFinding[];
  evaluation: EvaluationCounts | null;
  /** Rapor hazırlama isteği bu analizde hata verir (hata senaryosu). */
  reportFails?: boolean;
}

export const mockRunResults: Readonly<Record<number, RunResults>> = {
  1: { endpoints: [], tests: [], results: () => [], findings: [], evaluation: null },
  2: { endpoints: E2, tests: T2, results: run2Initial, findings: [], evaluation: null },
  3: { endpoints: [], tests: [], results: () => [], findings: [], evaluation: null },
  4: {
    endpoints: E4,
    tests: T4,
    results: () => R4.map((r) => ({ ...r })),
    findings: F4,
    evaluation: { tp: 3, fp: 1, fn: 1, tn: 7, ground_truth: 'DEMO referans kümesi (altın etiketli)' },
  },
  5: { endpoints: E5, tests: T5, results: () => R5.map((r) => ({ ...r })), findings: [], evaluation: null },
  6: {
    endpoints: E6,
    tests: T6,
    results: () => R6.map((r) => ({ ...r })),
    findings: F6,
    evaluation: null,
    reportFails: true,
  },
};

/** Canlı akışın bir adımı: sıradaki RUNNING testi bitirir, sıradaki PENDING testi başlatır. */
export function advanceRun2(results: readonly TestExecutionResult[]): TestExecutionResult[] {
  const next = results.map((r) => ({ ...r }));
  const running = next.find((r) => r.status === 'RUNNING');
  if (running) {
    const final = RUN2_FINAL[running.generated_test];
    if (final) Object.assign(running, final);
  }
  const pending = next.find((r) => r.status === 'PENDING');
  if (pending) pending.status = 'RUNNING';
  return next;
}

export function isRun2Finished(results: readonly TestExecutionResult[]): boolean {
  return results.every((r) => r.status !== 'RUNNING' && r.status !== 'PENDING');
}

export type { ExecutionSnapshot };
