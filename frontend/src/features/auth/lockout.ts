// Hesap kilidi yanıtının yorumlanması (H5-03 / #41). Güvenlik kararı backend'dedir (django-axes);
// burada yalnızca 429 yanıtının kilit mi istek sınırı mı olduğu ve sunucunun bildirdiği kalan süre okunur.
import type { ApiError } from '../../types';

export interface LockInfo {
  /** Sunucunun bildirdiği kalan süre (saniye); bilinmiyorsa null (geri sayım uydurulmaz). */
  retryAfterSeconds: number | null;
}

export function lockInfoFrom(error: ApiError): LockInfo | null {
  if (error.status !== 429) return null;
  const body = error.body as { code?: unknown; retry_after_seconds?: unknown };
  if (body.code !== 'account_locked') return null; // istek sınırı (throttle) 429'u
  const seconds = body.retry_after_seconds;
  return { retryAfterSeconds: typeof seconds === 'number' && seconds >= 0 ? seconds : null };
}

/** "14 dk 05 sn" / "45 sn". */
export function formatRemaining(seconds: number): string {
  const s = Math.max(0, Math.ceil(seconds));
  const minutes = Math.floor(s / 60);
  const rest = s % 60;
  return minutes > 0 ? `${minutes} dk ${String(rest).padStart(2, '0')} sn` : `${rest} sn`;
}
