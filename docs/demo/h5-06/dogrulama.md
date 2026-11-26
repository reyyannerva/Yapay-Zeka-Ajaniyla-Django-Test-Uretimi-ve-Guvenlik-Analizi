# H5-06 doğrulama ve kabul kriterleri eşlemesi · Issue #44

Bu belge, #44 kabul kriterlerini **gerçek, çalıştırılmış kanıtlarla** eşler. Hiçbir metrik
uydurulmamıştır; çalıştırılmamış hiçbir test "başarılı" raporlanmamıştır.

## Çalıştırılan doğrulamalar (2026-11-26, canlı yığın)

| Doğrulama | Komut | Sonuç |
|---|---|---|
| Backend test suite (PostgreSQL 16) | `backend> bvenv/Scripts/python.exe -m pytest -q` | **470 passed, 1 skipped** (0:03:49) |
| Frontend birim/entegrasyon testleri | `frontend> npm run test` (vitest) | **255 passed / 37 dosya** |
| Frontend üretim derlemesi | `frontend> npm run build` (tsc + vite) | **Başarılı** (tsc hatasız, vite build 4.68s) |
| Canlı API smoke testi | `python docs/demo/h5-06/scripts/live_smoke.py` | **10/10 adım geçti** (bkz. `evidence/live_smoke_result.json`) |
| PostgreSQL bağlantısı | `backend> manage.py check_database` | Bağlantı başarılı (PostgreSQL 16.16) |

> Not: Backend/frontend testleri daha önceki haftalarda da vardı; burada **bu makinede, bu commit'te
> gerçekten çalıştırılıp** geçtikleri doğrulanmıştır.

### Canlı smoke testi adımları (gerçek HTTP)

`demo_merve`/`demo_ikinci`/`demo_kilit` kullanıcılarıyla, çalışan backend'e (`127.0.0.1:8000`):

1. Giriş (JWT) → HTTP 200, access+refresh alındı.
2. Korumalı `/api/auth/me/` → HTTP 200 (`username=demo_merve`).
3. Proje listele (GET) → HTTP 200.
4. **Proje oluştur (POST multipart, `ornek-proje.zip`)** → HTTP 201.
5. Proje detay (GET) → HTTP 200.
6. Proje güncelle (PATCH) → HTTP 200.
7. **Sahiplik: ikinci kullanıcı başkasının projesini isteyince** → HTTP 404 (erişim engellendi).
8. Proje sil (DELETE) → HTTP 204.
9. Şifre sıfırlama talebi (POST) → HTTP 200.
10. **Hesap kilidi / kaba kuvvet koruması** (hatalı girişler) → 401, ardından 429 (engellendi).

## Kabul kriterleri eşlemesi

| # | Kabul kriteri | Durum | Kanıt |
|---|---|---|---|
| 1 | Ekranlar arası navigasyon + temel tasarım tutarlılığı | ✅ | 14 ekran görüntüsü (tek tasarım sistemi, koyu tema); frontend 255 test + build |
| 2 | JWT giriş, hesap kilidi, şifre sıfırlama, korumalı sayfa | ✅ | Smoke adım 1,2,9,10; backend test suite (axes 3-hata→15dk kilit testleri dahil); `ProtectedRoute` testleri |
| 3 | Proje yükleme + CRUD gerçek API ile canlı gösterime hazır | ✅ | Smoke adım 3–8 (POST/GET/PATCH/DELETE, 404 sahiplik); detay ekranı arşiv SHA-256 + doğrulama raporu |
| 4 | AnalysisRun + referans gereksinim API temel işlemleri | ✅ (kısmi: kayıt) | Proje detayında AnalysisRun QUEUED oluşturma + referans JSON yükleme; `referans-gereksinimler.json` 5 metot; backend API testleri. **Analiz yürütme motoru prototiptir** (bkz. gercek-vs-prototip) |
| 5 | Gerçek çalışan özellikler ↔ mock/prototip ayrımı | ✅ | [`gercek-vs-prototip.md`](gercek-vs-prototip.md); DEMO ekranları "DEMO/Örnek veri" rozetli (ss 09–14) |
| 6 | Kural tabanlı / LLM / hibrit sonuçlar sunulabilir | ✅ | [`karsilastirma-tablosu.md`](karsilastirma-tablosu.md) (H5-04 + H5-05 gerçek çıktıları) |
| 7 | Canlı demo sırası + güvenli örnek veriler + kurulum | ✅ | [`README.md`](README.md) §1–4; `demo-verileri/` |
| 8 | Kritik demo hataları giderilmiş veya belgelenmiş | ✅ | [`bilinen-sinirliliklar.md`](bilinen-sinirliliklar.md) |
| 9 | Demo yönergeleri, ss, karşılaştırma tablosu, kanıtlar repoda | ✅ | Bu `docs/demo/h5-06/` paketi |

## Yapılacaklar maddeleri — not düşülenler

- **"5 HTTP metodu referans JSON'da desteklenir"**: `referans-gereksinimler.json` GET/POST/PUT/PATCH/
  DELETE içerir; backend `ck_reference_requirements_access_rule_method` kısıtı ve serializer bunu
  zorlar (backend testleri).
- **Hesap kilidi**: Canlı smoke'ta kaba kuvvet koruması 401→429 ile gözlendi; **3 hatalı giriş → 403
  / 15 dk axes kilidi** davranışının birebir doğruluğu backend test suite'inde (470 test) doğrulanır.
  Oran sınırlayıcı (throttle) ile axes kilidi birlikte korumayı sağlar.
- **Boş/yükleniyor/hata/DEMO durumları**: DEMO analiz ekranlarında boş durum mesajları görülür
  (ss 13 "Güvenlik taraması henüz tamamlanmadı", ss 04 "Henüz analiz yok"); frontend testleri bu
  durumları kapsar.
