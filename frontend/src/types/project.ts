// docs/api/projects.md — Project bileşeni
export type ProjectValidationStatus = 'PENDING' | 'VALID' | 'INVALID';
export type ProjectSourceType = 'ARCHIVE' | 'ALLOWED_DIRECTORY';

export interface ArchiveInfo {
  original_name: string;
  size_bytes: number;
  sha256: string;
  /** ISO 8601 tarih-saat */
  uploaded_at: string;
}

/** Sunucunun arşiv doğrulama raporu; şema sürümlü, serbest biçimli JSON. */
export interface ProjectValidationReport {
  schema_version?: number;
  warnings?: string[];
  checked_at?: string;
  django_apps?: string[];
  drf_detected?: boolean;
  manage_py_found?: boolean;
  manage_py_paths?: string[];
  rejected_entries?: { path: string; reason: string }[];
  settings_modules?: string[];
  installed_apps_count?: number;
  declared_settings_modules?: string[];
  [key: string]: unknown;
}

export interface Project {
  id: number;
  name: string;
  description: string;
  source_type: ProjectSourceType;
  validation_status: ProjectValidationStatus;
  archive: ArchiveInfo | null;
  validation_report: ProjectValidationReport | null;
  analysis_run_count: number;
  created_at: string;
  updated_at: string;
}

export interface PaginatedProjectList {
  count: number;
  next: string | null;
  previous: string | null;
  results: Project[];
}

/** POST /api/projects/ — multipart/form-data alanları. */
export interface ProjectCreateInput {
  name: string;
  description?: string;
  archive: File;
}

/** PUT/PATCH /api/projects/{id}/ — yalnızca bu iki alan güncellenebilir. */
export interface ProjectUpdateInput {
  name?: string;
  description?: string;
}
