// API bağlantı yapılandırması (H5-03 / #41). Değerler Vite ortam değişkenlerinden okunur.
// VITE_ ile başlayan değişkenler derlenen pakete gömülür ve tarayıcıda görünür; gizli değer konmaz.

const DEFAULT_API_BASE_URL = 'http://localhost:8000';

/** Sondaki eğik çizgiler atılır; boş değerde geliştirme varsayılanı kullanılır. */
export function normalizeBaseUrl(raw: string | undefined): string {
  const value = (raw ?? '').trim();
  return (value || DEFAULT_API_BASE_URL).replace(/\/+$/, '');
}

export const API_BASE_URL = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL);

/** Varsayılan istek zaman aşımı. */
export const API_TIMEOUT_MS = 20_000;
/** Arşiv yükleme gibi büyük gövdeli istekler için zaman aşımı. */
export const UPLOAD_TIMEOUT_MS = 120_000;
