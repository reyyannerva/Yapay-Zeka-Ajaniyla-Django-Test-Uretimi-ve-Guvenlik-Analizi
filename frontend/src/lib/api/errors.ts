// API hatalarının kullanıcı mesajına çevrilmesi (H5-03 / #41). Tek kaynak; ekranlar durum koduna göre
// kendi metinlerini üretmez. Sunucu ayrıntısı (stack trace vb.) istemcide zaten genel mesaja çevrilir.
import type { ApiError } from '../../types';
import { SERVER_ERROR_DETAIL, isApiError } from './client';

function detailOf(error: ApiError): string | undefined {
  const detail = (error.body as { detail?: unknown }).detail;
  return typeof detail === 'string' ? detail : undefined;
}

/** Durum koduna göre kısa ve güvenli Türkçe mesaj. */
export function errorMessage(error: unknown): string {
  if (!isApiError(error)) return 'Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.';
  switch (error.status) {
    case 0:
      return detailOf(error) ?? 'Sunucuya bağlanılamadı.';
    case 400:
      return 'Gönderilen bilgiler geçersiz. Lütfen işaretli alanları düzeltin.';
    case 401:
      return 'Oturumunuz sona erdi. Lütfen yeniden giriş yapın.';
    case 403:
      return 'Bu işlem için yetkiniz yok.';
    case 404:
      return 'Kayıt bulunamadı veya bu kayda erişim yetkiniz yok.';
    case 409:
      return detailOf(error) ?? 'Bu işlem şu anda yapılamıyor.';
    case 413:
      return 'Gönderilen dosya izin verilen boyutu aşıyor.';
    case 415:
      return 'İstek biçimi sunucu tarafından desteklenmiyor.';
    case 429:
      return 'Kısa sürede çok fazla istek gönderildi. Lütfen biraz bekleyip tekrar deneyin.';
    default:
      return error.status >= 500 ? SERVER_ERROR_DETAIL : `İstek başarısız oldu (HTTP ${error.status}).`;
  }
}

/** DRF 400 gövdesini alan yolu → ilk mesaj eşlemesine düzleştirir (iç içe: "specification.method"). */
export function flattenFieldErrors(body: unknown, prefix = ''): Record<string, string> {
  const out: Record<string, string> = {};
  if (Array.isArray(body)) {
    const first = body[0];
    if (typeof first === 'string') out[prefix || 'non_field_errors'] = first;
    else if (first && typeof first === 'object') Object.assign(out, flattenFieldErrors(first, prefix));
    return out;
  }
  if (typeof body === 'string') {
    out[prefix || 'non_field_errors'] = body;
    return out;
  }
  if (body && typeof body === 'object') {
    for (const [key, value] of Object.entries(body as Record<string, unknown>)) {
      if (key === 'detail' && !prefix) continue;
      Object.assign(out, flattenFieldErrors(value, prefix ? `${prefix}.${key}` : key));
    }
  }
  return out;
}
