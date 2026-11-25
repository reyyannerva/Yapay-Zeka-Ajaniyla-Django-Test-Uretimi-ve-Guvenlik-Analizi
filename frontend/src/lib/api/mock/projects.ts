// AÇIKÇA ÖRNEK VERİ — gerçek bir projeyi, arşivi veya özeti temsil etmez.
import type { ApiError, Project } from '../../../types';

const PLACEHOLDER_SHA256 = '0'.repeat(64);

export function createSampleProjects(): Project[] {
  return [
    {
      id: 3,
      name: 'Örnek Proje C',
      description: 'Örnek veri: doğrulaması bekleyen proje.',
      source_type: 'ARCHIVE',
      validation_status: 'PENDING',
      archive: {
        original_name: 'ornek-c.zip',
        size_bytes: 1024,
        sha256: PLACEHOLDER_SHA256,
        uploaded_at: '2026-03-03T10:00:00Z',
      },
      validation_report: null,
      analysis_run_count: 0,
      created_at: '2026-03-03T10:00:00Z',
      updated_at: '2026-03-03T10:00:00Z',
    },
    {
      id: 2,
      name: 'Örnek Proje B',
      description: 'Örnek veri: doğrulaması başarısız proje.',
      source_type: 'ARCHIVE',
      validation_status: 'INVALID',
      archive: {
        original_name: 'ornek-b.zip',
        size_bytes: 2048,
        sha256: PLACEHOLDER_SHA256,
        uploaded_at: '2026-02-02T10:00:00Z',
      },
      validation_report: {
        schema_version: 1,
        warnings: [],
        manage_py_found: false,
        rejected_entries: [{ path: 'ornek/yol', reason: 'PATH_TRAVERSAL' }],
      },
      analysis_run_count: 0,
      created_at: '2026-02-02T10:00:00Z',
      updated_at: '2026-02-02T10:00:00Z',
    },
    {
      id: 1,
      name: 'Örnek Proje A',
      description: 'Örnek veri: doğrulanmış proje.',
      source_type: 'ARCHIVE',
      validation_status: 'VALID',
      archive: {
        original_name: 'ornek-a.zip',
        size_bytes: 4096,
        sha256: PLACEHOLDER_SHA256,
        uploaded_at: '2026-01-01T10:00:00Z',
      },
      validation_report: {
        schema_version: 1,
        warnings: [],
        manage_py_found: true,
        drf_detected: true,
        django_apps: ['ornek_uygulama'],
        rejected_entries: [],
      },
      analysis_run_count: 3,
      created_at: '2026-01-01T10:00:00Z',
      updated_at: '2026-01-01T10:00:00Z',
    },
  ];
}

/** Bellek içi, değiştirilebilir mock depo (sayfa yenilenince sıfırlanır). */
export const mockProjectStore: { projects: Project[]; nextId: number } = {
  projects: createSampleProjects(),
  nextId: 4,
};

export function resetMockProjects(): void {
  mockProjectStore.projects = createSampleProjects();
  mockProjectStore.nextId = 4;
}

/** Başka kullanıcıya ait (erişilemeyen) projeyi simüle eden sabit kimlik; gerçek 403 yolu #41'de. */
export const MOCK_FORBIDDEN_PROJECT_ID = 9403;

export function mockForbidden(): ApiError {
  return { status: 403, body: { detail: 'Bu işlem için yetkiniz yok.' } };
}

export function mockNotFound(): ApiError {
  return { status: 404, body: { detail: 'No Project matches the given query.' } };
}
