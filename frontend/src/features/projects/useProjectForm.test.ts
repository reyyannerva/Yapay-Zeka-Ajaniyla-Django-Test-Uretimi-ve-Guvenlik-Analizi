import { expect, test } from 'vitest';

import { translateProjectError } from './useProjectForm';

test('413 yanıtı boyut sınırını anlatan mesaja çevrilir', () => {
  const result = translateProjectError({
    status: 413,
    body: { detail: 'Yüklenen dosya en fazla 52428800 bayt olabilir.' },
  });
  expect(result.message).toMatch(/50 MiB/);
});

test('arşiv doğrulama hatası (PATH_TRAVERSAL) anlaşılır mesaja çevrilir', () => {
  const result = translateProjectError({
    status: 400,
    body: { archive: [{ code: 'PATH_TRAVERSAL', detail: 'ham', entries: [] }] },
  });
  expect(result.message).toMatch(/üst dizin/i);
});

test('ad alanı hatası alan hatası olarak ayrılır', () => {
  const result = translateProjectError({
    status: 400,
    body: { name: ['Bu adla kayıtlı bir projeniz zaten var.'] },
  });
  expect(result.fieldErrors?.name).toBe('Bu adla kayıtlı bir projeniz zaten var.');
});

test('409 yanıtı sunucu mesajını korur', () => {
  const result = translateProjectError({
    status: 409,
    body: { detail: 'Projenin devam eden bir analizi var; analiz bitmeden proje silinemez.' },
  });
  expect(result.message).toMatch(/devam eden bir analizi/);
});

test('bilinmeyen hata çökmeden genel mesaj verir', () => {
  expect(translateProjectError(new Error('boom')).message).toMatch(/tekrar deneyin/i);
  expect(translateProjectError({ status: 415, body: { detail: 'x' } }).message).toMatch(/form/i);
});
