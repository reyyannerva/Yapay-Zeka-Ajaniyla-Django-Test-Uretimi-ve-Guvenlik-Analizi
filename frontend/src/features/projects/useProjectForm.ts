import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { isApiError } from '../../lib/api/client';
import type { ArchiveErrorCode } from '../../types';

/** Sunucu sınırı: 52428800 bayt (docs/api/projects.md, 413). */
export const MAX_ARCHIVE_BYTES = 50 * 1024 * 1024;
const MAX_NAME_LENGTH = 150; // docs/database/data_dictionary.md: varchar(150)

// Tarayıcı/işletim sistemi .zip için farklı MIME türleri bildirebilir; boş tür de olağandır.
const ZIP_MIME_TYPES = new Set([
  '',
  'application/zip',
  'application/x-zip-compressed',
  'application/x-zip',
  'application/octet-stream',
]);

function isZip(file: File): boolean {
  return file.name.toLowerCase().endsWith('.zip') && ZIP_MIME_TYPES.has(file.type);
}

function formatMiB(bytes: number): string {
  return (bytes / (1024 * 1024)).toLocaleString('tr-TR', { maximumFractionDigits: 1 });
}

const nameField = z
  .string()
  .trim()
  .min(1, 'Proje adı zorunludur.')
  .max(MAX_NAME_LENGTH, `Proje adı en fazla ${MAX_NAME_LENGTH} karakter olabilir.`);

const descriptionField = z.string().trim();

const archiveField = z
  .custom<File>((value) => value instanceof File, 'Bir .zip arşivi seçin.')
  .refine((file) => isZip(file), 'Yalnızca .zip uzantılı arşivler yüklenebilir.')
  .refine((file) => file.size > 0, 'Seçilen arşiv boş.')
  .refine(
    (file) => file.size <= MAX_ARCHIVE_BYTES,
    (file) => ({
      message: `Arşiv en fazla 50 MiB olabilir (seçilen: ${formatMiB(file.size)} MiB).`,
    }),
  );

export const projectUploadSchema = z.object({
  name: nameField,
  description: descriptionField,
  archive: archiveField,
});

/** Düzenleme: yalnızca ad ve açıklama; arşiv değiştirilemez (docs/api/projects.md). */
export const projectEditSchema = z.object({
  name: nameField,
  description: descriptionField,
});

export type ProjectUploadValues = z.infer<typeof projectUploadSchema>;
export type ProjectEditValues = z.infer<typeof projectEditSchema>;

export function useProjectForm() {
  return useForm<ProjectUploadValues>({
    resolver: zodResolver(projectUploadSchema),
    defaultValues: { name: '', description: '' },
  });
}

export function useProjectEditForm(defaults: ProjectEditValues) {
  return useForm<ProjectEditValues>({
    resolver: zodResolver(projectEditSchema),
    defaultValues: defaults,
  });
}

// --- Sunucu hatalarını kullanıcıya anlaşılır mesaja çevirme ---

const ARCHIVE_MESSAGES: Partial<Record<ArchiveErrorCode, string>> = {
  UNSUPPORTED_TYPE: 'Yalnızca .zip uzantılı arşivler yüklenebilir.',
  EMPTY_FILE: 'Seçilen arşiv boş.',
  NOT_A_ZIP: 'Dosya geçerli bir ZIP arşivi değil.',
  CORRUPT_ARCHIVE: 'Arşiv bozuk görünüyor; dosyayı yeniden oluşturup deneyin.',
  ENCRYPTED: 'Parola korumalı arşivler desteklenmez.',
  EMPTY_ARCHIVE: 'Arşivin içinde dosya yok.',
  FILE_TOO_LARGE: 'Arşiv en fazla 50 MiB olabilir.',
  TOO_MANY_ENTRIES: 'Arşivdeki dosya sayısı izin verilen sınırı aşıyor.',
  PATH_TRAVERSAL: 'Arşiv, üst dizine çıkan güvenli olmayan bir dosya yolu içeriyor.',
  ABSOLUTE_PATH: 'Arşiv, mutlak dosya yolları içeriyor; yolların arşiv köküne göre olması gerekir.',
  SYMLINK: 'Arşiv sembolik bağlantı içeriyor; bu desteklenmez.',
  UNCOMPRESSED_TOO_LARGE: 'Arşivin açılmış boyutu izin verilen sınırı aşıyor.',
  COMPRESSION_RATIO: 'Arşivin sıkıştırma oranı olağan dışı yüksek; güvenlik nedeniyle reddedildi.',
  NO_DJANGO_SETTINGS: 'Arşivde bir Django ayar modülü bulunamadı.',
  NO_DJANGO_ENTRYPOINT: 'Arşivde manage.py bulunamadı; bir Django projesi yükleyin.',
  UNSAFE_ARCHIVE: 'Arşiv güvenlik denetimini geçemedi.',
};

const GENERIC_MESSAGE = 'İşlem tamamlanamadı. Lütfen daha sonra tekrar deneyin.';

export interface TranslatedProjectError {
  /** Kullanıcıya gösterilecek anlaşılır mesaj. */
  message: string;
  /** Sunucunun alana özgü bildirdiği hatalar (forma bağlanır). */
  fieldErrors?: { name?: string; description?: string; archive?: string };
}

function firstString(value: unknown): string | undefined {
  if (!Array.isArray(value) || value.length === 0) return undefined;
  return typeof value[0] === 'string' ? value[0] : undefined;
}

function archiveMessage(value: unknown): string | undefined {
  if (!Array.isArray(value) || value.length === 0) return undefined;
  const first: unknown = value[0];
  if (typeof first === 'string') return first;
  if (typeof first === 'object' && first !== null) {
    const { code, detail } = first as { code?: ArchiveErrorCode; detail?: string };
    return (code && ARCHIVE_MESSAGES[code]) || detail || 'Arşiv doğrulanamadı.';
  }
  return undefined;
}

/** 400/404/409/413/415 ve bilinmeyen hataları form için anlaşılır mesaja çevirir; asla fırlatmaz. */
export function translateProjectError(error: unknown): TranslatedProjectError {
  if (!isApiError(error)) return { message: GENERIC_MESSAGE };
  const body = error.body as Record<string, unknown>;

  switch (error.status) {
    case 413:
      return { message: 'Arşiv sunucunun kabul ettiği en büyük boyutu (50 MiB) aşıyor.' };
    case 415:
      return { message: 'İstek biçimi desteklenmiyor; yükleme multipart form verisiyle yapılmalıdır.' };
    case 404:
      return { message: 'Proje bulunamadı; silinmiş olabilir.' };
    case 409:
      return {
        message: typeof body.detail === 'string' ? body.detail : 'Bu işlem şu anda yapılamıyor.',
      };
    case 400: {
      const fieldErrors: NonNullable<TranslatedProjectError['fieldErrors']> = {};
      const name = firstString(body.name);
      const description = firstString(body.description);
      const archive = archiveMessage(body.archive);
      if (name) fieldErrors.name = name;
      if (description) fieldErrors.description = description;
      if (archive) fieldErrors.archive = archive;
      const message = archive ?? name ?? description ?? firstString(body.non_field_errors);
      return { message: message ?? 'Gönderilen bilgiler geçerli değil.', fieldErrors };
    }
    default:
      return { message: typeof body.detail === 'string' ? body.detail : GENERIC_MESSAGE };
  }
}
