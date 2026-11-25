// Referans gereksinim servisi (H5-03 / #41) — backend/core/api (ReferenceRequirementViewSet, ModelViewSet).
// GET/POST/PUT/PATCH/DELETE; doğrulama (kategori, specification, ACCESS_RULE method) sunucudadır.
import type { ReferenceRequirement, ReferenceRequirementInput } from '../../types';
import { apiFetch } from './client';

/** GET /api/reference-requirements/ — kullanıcının tüm referans kayıtları (sayfalama yok). */
export function listReferenceRequirements(signal?: AbortSignal): Promise<ReferenceRequirement[]> {
  return apiFetch<ReferenceRequirement[]>('/api/reference-requirements/', { signal });
}

export function getReferenceRequirement(id: number, signal?: AbortSignal): Promise<ReferenceRequirement> {
  return apiFetch<ReferenceRequirement>(`/api/reference-requirements/${id}/`, { signal });
}

/** POST — 201; başkasının projesi 400 `project`. */
export function createReferenceRequirement(input: ReferenceRequirementInput): Promise<ReferenceRequirement> {
  return apiFetch<ReferenceRequirement>('/api/reference-requirements/', { method: 'POST', body: { ...input } });
}

/** PUT — tam güncelleme (revision sunucuda artırılır). */
export function replaceReferenceRequirement(id: number, input: ReferenceRequirementInput): Promise<ReferenceRequirement> {
  return apiFetch<ReferenceRequirement>(`/api/reference-requirements/${id}/`, { method: 'PUT', body: { ...input } });
}

/** PATCH — kısmi güncelleme (ör. is_active). */
export function patchReferenceRequirement(
  id: number,
  patch: Partial<ReferenceRequirementInput>,
): Promise<ReferenceRequirement> {
  return apiFetch<ReferenceRequirement>(`/api/reference-requirements/${id}/`, { method: 'PATCH', body: { ...patch } });
}

/** DELETE — 204. */
export function deleteReferenceRequirement(id: number): Promise<void> {
  return apiFetch<void>(`/api/reference-requirements/${id}/`, { method: 'DELETE' });
}
