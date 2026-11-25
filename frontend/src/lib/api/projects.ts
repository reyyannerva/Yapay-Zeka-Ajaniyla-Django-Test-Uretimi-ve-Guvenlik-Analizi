// Proje servisi (H5-03 / #41) — backend/core/projects (DRF ProjectViewSet).
// Sahiplik sunucudadır: liste yalnızca kullanıcının projelerini döndürür, başkasının projesi 404'tür.
import type { PaginatedProjectList, Project, ProjectCreateInput, ProjectUpdateInput } from '../../types';
import { apiFetch } from './client';
import { UPLOAD_TIMEOUT_MS } from './config';

/** GET /api/projects/?page=&page_size= — 200, sayfalı (varsayılan 20, en fazla 100), en yeni önce. */
export function listProjects(
  params?: { page?: number; page_size?: number },
  signal?: AbortSignal,
): Promise<PaginatedProjectList> {
  const query = new URLSearchParams();
  if (params?.page) query.set('page', String(params.page));
  if (params?.page_size) query.set('page_size', String(params.page_size));
  const suffix = query.toString() ? `?${query.toString()}` : '';
  return apiFetch<PaginatedProjectList>(`/api/projects/${suffix}`, { signal });
}

/** GET /api/projects/{id}/ — 200; yoksa veya başkasına aitse 404. */
export function getProject(id: number, signal?: AbortSignal): Promise<Project> {
  return apiFetch<Project>(`/api/projects/${id}/`, { signal });
}

/**
 * POST /api/projects/ (multipart/form-data: name, description, archive) — 201.
 * Content-Type ve boundary tarayıcı tarafından üretilir (FormData). Arşiv doğrulaması sunucudadır.
 */
export function createProject(input: ProjectCreateInput): Promise<Project> {
  const form = new FormData();
  form.append('name', input.name);
  if (input.description) form.append('description', input.description);
  form.append('archive', input.archive, input.archive.name);
  return apiFetch<Project>('/api/projects/', { method: 'POST', body: form, timeoutMs: UPLOAD_TIMEOUT_MS });
}

/** PATCH /api/projects/{id}/ — yalnızca name/description; diğer alanlar sunucuda 400 ile reddedilir. */
export function updateProject(id: number, patch: ProjectUpdateInput): Promise<Project> {
  const body: Record<string, string> = {};
  if (patch.name !== undefined) body.name = patch.name;
  if (patch.description !== undefined) body.description = patch.description;
  return apiFetch<Project>(`/api/projects/${id}/`, { method: 'PATCH', body });
}

/** DELETE /api/projects/{id}/ — 204; aktif analiz varsa 409. Bağlı analiz ve referans kayıtları CASCADE silinir. */
export function deleteProject(id: number): Promise<void> {
  return apiFetch<void>(`/api/projects/${id}/`, { method: 'DELETE' });
}
