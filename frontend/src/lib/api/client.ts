import type { ApiError } from '../../types';

export interface ApiFetchInit extends Omit<RequestInit, 'body'> {
  /** JSON gövde veya multipart için FormData. */
  body?: BodyInit | Record<string, unknown> | null;
}

/** Servis katmanındaki reddedilen hata değerinin ApiError olup olmadığını söyler. */
export function isApiError(value: unknown): value is ApiError {
  return (
    typeof value === 'object' &&
    value !== null &&
    'status' in value &&
    typeof (value as { status: unknown }).status === 'number' &&
    'body' in value
  );
}

/**
 * Gerçek HTTP istemcisi için imza yer tutucusu. Gövdesi #41'de (gerçek API
 * entegrasyonu) doldurulacak; şimdilik hiçbir servis bunu çağırmaz, tüm
 * servisler `mock/` fixture'larını döndürür.
 */
export function apiFetch<T>(_path: string, _init?: ApiFetchInit): Promise<T> {
  return Promise.reject(new Error('apiFetch henüz uygulanmadı (#41 kapsamındadır).'));
}
