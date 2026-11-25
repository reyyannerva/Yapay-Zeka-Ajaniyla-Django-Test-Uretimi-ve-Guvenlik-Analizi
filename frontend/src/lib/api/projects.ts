import type {
  ApiError,
  PaginatedProjectList,
  Project,
  ProjectCreateInput,
  ProjectUpdateInput,
} from '../../types';
import {
  MOCK_FORBIDDEN_PROJECT_ID,
  mockAnalysisRuns,
  mockForbidden,
  mockNotFound,
  mockProjectStore,
} from './mock';

// Mock servis: bellek içi depo. Gerçek HTTP çağrısı #41'de.
// Kimlikler Django pk'sı gibi `number`'dır (docs/api/openapi.yaml: integer).

// Sunucu sınırları (docs/api/projects.md); mock bunları simüle eder.
const MAX_ARCHIVE_BYTES = 52_428_800;
const DUPLICATE_NAME = 'Bu adla kayıtlı bir projeniz zaten var.';
const ACTIVE_RUN_CONFLICT =
  'Projenin devam eden bir analizi var; analiz bitmeden proje silinemez.';
const FINISHED_STATUSES = ['COMPLETED', 'FAILED', 'CANCELLED'];

function hasDuplicateName(name: string, exceptId?: number): boolean {
  return mockProjectStore.projects.some((p) => p.name === name && p.id !== exceptId);
}

function hasActiveRun(projectId: number): boolean {
  return mockAnalysisRuns.some(
    (run) => run.project === projectId && !FINISHED_STATUSES.includes(run.status),
  );
}

function duplicateNameError(): ApiError {
  return { status: 400, body: { name: [DUPLICATE_NAME] } };
}

function newestFirst(a: Project, b: Project): number {
  return b.created_at.localeCompare(a.created_at);
}

export function listProjects(params?: {
  page?: number;
  page_size?: number;
}): Promise<PaginatedProjectList> {
  const pageSize = Math.min(params?.page_size ?? 20, 100);
  const page = params?.page ?? 1;
  const sorted = [...mockProjectStore.projects].sort(newestFirst);
  const start = (page - 1) * pageSize;
  return Promise.resolve({
    count: sorted.length,
    next: start + pageSize < sorted.length ? `?page=${page + 1}` : null,
    previous: page > 1 ? `?page=${page - 1}` : null,
    results: sorted.slice(start, start + pageSize),
  });
}

export function getProject(id: number): Promise<Project> {
  if (id === MOCK_FORBIDDEN_PROJECT_ID) return Promise.reject(mockForbidden());
  const found = mockProjectStore.projects.find((p) => p.id === id);
  return found ? Promise.resolve({ ...found }) : Promise.reject(mockNotFound());
}

export function createProject(input: ProjectCreateInput): Promise<Project> {
  if (input.archive.size > MAX_ARCHIVE_BYTES) {
    return Promise.reject<Project>({
      status: 413,
      body: { detail: `Yüklenen dosya en fazla ${MAX_ARCHIVE_BYTES} bayt olabilir.` },
    } satisfies ApiError);
  }
  if (!input.archive.name.toLowerCase().endsWith('.zip')) {
    return Promise.reject<Project>({
      status: 400,
      body: {
        archive: [
          { code: 'UNSUPPORTED_TYPE', detail: 'Yalnızca .zip arşivleri kabul edilir.' },
        ],
      },
    } satisfies ApiError);
  }
  if (hasDuplicateName(input.name)) return Promise.reject(duplicateNameError());
  const now = new Date().toISOString();
  const project: Project = {
    id: mockProjectStore.nextId++,
    name: input.name,
    description: input.description ?? '',
    source_type: 'ARCHIVE',
    validation_status: 'PENDING',
    archive: {
      original_name: input.archive.name,
      size_bytes: input.archive.size,
      sha256: '0'.repeat(64),
      uploaded_at: now,
    },
    validation_report: null,
    analysis_run_count: 0,
    created_at: now,
    updated_at: now,
  };
  mockProjectStore.projects.push(project);
  return Promise.resolve({ ...project });
}

export function updateProject(id: number, patch: ProjectUpdateInput): Promise<Project> {
  const found = mockProjectStore.projects.find((p) => p.id === id);
  if (!found) return Promise.reject(mockNotFound());
  if (patch.name !== undefined && hasDuplicateName(patch.name, id)) {
    return Promise.reject(duplicateNameError());
  }
  if (patch.name !== undefined) found.name = patch.name;
  if (patch.description !== undefined) found.description = patch.description;
  found.updated_at = new Date().toISOString();
  return Promise.resolve({ ...found });
}

export function deleteProject(id: number): Promise<void> {
  const index = mockProjectStore.projects.findIndex((p) => p.id === id);
  if (index === -1) return Promise.reject(mockNotFound());
  if (hasActiveRun(id)) {
    return Promise.reject({ status: 409, body: { detail: ACTIVE_RUN_CONFLICT } } satisfies ApiError);
  }
  mockProjectStore.projects.splice(index, 1);
  return Promise.resolve();
}
