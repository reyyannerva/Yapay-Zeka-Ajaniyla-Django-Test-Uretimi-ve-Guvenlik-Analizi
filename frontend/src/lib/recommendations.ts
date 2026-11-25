// Düzeltme önerisi kataloğu (#40). Backend bulguya yalnızca `recommendation_key` yazar;
// metin buradan gelir. Bilinmeyen veya boş anahtar için öneri uydurulmaz (null döner).
export interface Recommendation {
  title: string;
  text: string;
  /** İlgili kontrol veya kaynak. */
  reference: string;
}

const CATALOG: Readonly<Record<string, Recommendation>> = {
  OBJECT_LEVEL_AUTHZ: {
    title: 'Nesne düzeyinde yetkilendirme ekleyin',
    text: 'Sorguyu istek sahibinin kayıtlarıyla sınırlayın (get_queryset) veya has_object_permission uygulayan bir izin sınıfı kullanın.',
    reference: 'OWASP API Security Top 10 — API1:2023 Broken Object Level Authorization',
  },
  STAFF_ONLY_VIEW: {
    title: 'Yönetim görünümünü personelle sınırlayın',
    text: 'Görünüme IsAdminUser izni veya staff_member_required dekoratörü ekleyin.',
    reference: 'Django REST framework — Permissions (IsAdminUser)',
  },
  DEBUG_DISABLED: {
    title: 'Canlı ortamda DEBUG kapatılmalı',
    text: 'DEBUG değerini ortam değişkeninden okuyun ve canlı ortamda False olarak ayarlayın.',
    reference: 'Django deployment checklist — security.W018',
  },
  SUBPROCESS_NO_SHELL: {
    title: 'Komutları kabuk olmadan çalıştırın',
    text: 'subprocess çağrılarında shell=True kullanmayın; komutu argüman listesi olarak verin.',
    reference: 'Bandit B602 — subprocess_popen_with_shell_equals_true',
  },
};

export function getRecommendation(key: string | null): Recommendation | null {
  if (!key) return null;
  return CATALOG[key] ?? null;
}
