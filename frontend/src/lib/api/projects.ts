import type {
  PaginatedProjectList,
  Project,
  ProjectCreateInput,
  ProjectUpdateInput,
} from '../../types';
import { mockNotFound, mockProjectStore } from './mock';

// Mock servis: bellek içi depo. Gerçek HTTP çağrısı #41'de.
// Kimlikler Django pk'sı gibi `number`'dır (docs/api/openapi.yaml: integer).

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
  const found = mockProjectStore.projects.find((p) => p.id === id);
  return found ? Promise.resolve({ ...found }) : Promise.reject(mockNotFound());
}

export function createProject(input: ProjectCreateInput): Promise<Project> {
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
  if (patch.name !== undefined) found.name = patch.name;
  if (patch.description !== undefined) found.description = patch.description;
  found.updated_at = new Date().toISOString();
  return Promise.resolve({ ...found });
}

export function deleteProject(id: number): Promise<void> {
  const index = mockProjectStore.projects.findIndex((p) => p.id === id);
  if (index === -1) return Promise.reject(mockNotFound());
  mockProjectStore.projects.splice(index, 1);
  return Promise.resolve();
}
