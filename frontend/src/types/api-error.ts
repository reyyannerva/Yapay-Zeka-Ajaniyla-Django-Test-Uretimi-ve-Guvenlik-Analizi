// docs/api/projects.md + authentication.md — hata zarfları
export type ArchiveErrorCode =
  | 'UNSUPPORTED_TYPE'
  | 'EMPTY_FILE'
  | 'NOT_A_ZIP'
  | 'CORRUPT_ARCHIVE'
  | 'UNSUPPORTED_COMPRESSION'
  | 'ENCRYPTED'
  | 'EMPTY_ARCHIVE'
  | 'FILE_TOO_LARGE'
  | 'TOO_MANY_ENTRIES'
  | 'PATH_TRAVERSAL'
  | 'BACKSLASH_PATH'
  | 'ABSOLUTE_PATH'
  | 'DRIVE_PATH'
  | 'UNC_PATH'
  | 'INVALID_NAME'
  | 'RESERVED_NAME'
  | 'SYMLINK'
  | 'SPECIAL_FILE'
  | 'DUPLICATE_PATH'
  | 'CASE_COLLISION'
  | 'PATH_CONFLICT'
  | 'PATH_TOO_LONG'
  | 'TOO_DEEP'
  | 'MEMBER_TOO_LARGE'
  | 'UNCOMPRESSED_TOO_LARGE'
  | 'COMPRESSION_RATIO'
  | 'NO_DJANGO_SETTINGS'
  | 'NO_DJANGO_ENTRYPOINT'
  | 'UNSAFE_ARCHIVE';

export interface ArchiveErrorEntry {
  path: string;
  /** ArchiveErrorCode değerlerinden biri veya 'CORRUPT_MEMBER' */
  reason: ArchiveErrorCode | 'CORRUPT_MEMBER';
}

export interface ArchiveFieldError {
  code: ArchiveErrorCode;
  detail: string;
  entries?: ArchiveErrorEntry[];
}

/** 401/403/404/405/409/413/415/429/500 — `{ detail }` (token hatalarında `code` da olabilir). */
export interface DetailErrorBody {
  detail: string;
  code?: string;
}

/** 400 — arşiv doğrulama hatası: `{ archive: [{ code, detail, entries }] }`. */
export interface ArchiveErrorBody {
  archive: ArchiveFieldError[];
}

/** 400 — alan hataları: `{ alan: ["mesaj", ...] }` (non_field_errors dahil). */
export type FieldErrorsBody = Record<string, string[]>;

export type ApiErrorBody = DetailErrorBody | ArchiveErrorBody | FieldErrorsBody;

export type ApiErrorStatus = 400 | 401 | 403 | 404 | 405 | 409 | 413 | 415 | 429 | 500;

/** Servis katmanının reddettiği hata: HTTP durumu + gövde zarfı. */
export interface ApiError {
  status: ApiErrorStatus;
  body: ApiErrorBody;
}
