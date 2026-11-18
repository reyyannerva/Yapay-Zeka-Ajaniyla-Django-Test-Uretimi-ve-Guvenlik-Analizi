# API Dokümantasyonu — Hafta 4 (H4-05 / Issue #37)

Bu dizin, Hafta 4 backend API'sinin (H4-02 kimlik doğrulama, H4-03 proje yükleme/yönetimi, H4-04 analiz ve
referans gereksinimler) **koddan üretilen** OpenAPI 3.0.3 belgesini ve kullanım kılavuzlarını içerir. Şema
`drf-spectacular` ile doğrudan görünümlerden/serializer'lardan üretilir; elle yazılmış ayrı bir sözleşme yoktur.

| Dosya | İçerik |
|---|---|
| [`openapi.yaml`](openapi.yaml) / [`openapi.json`](openapi.json) | Dışa aktarılmış şema (aynı içerik, iki biçim) |
| [`authentication.md`](authentication.md) | JWT, token yenileme/rotasyon, çıkış, hesap kilidi, şifre sıfırlama |
| [`projects.md`](projects.md) | Proje oluşturma (multipart ZIP), listeleme, güncelleme, silme, arşiv hataları |
| [`analysis.md`](analysis.md) | AnalysisRun oluşturma/izleme, 9 durum, ilerleme alanları |
| [`reference-requirements.md`](reference-requirements.md) | Referans gereksinim CRUD'u, `specification` yapıları, HTTP yöntem enum'u |
| [`postman_collection.json`](postman_collection.json) | Postman v2.1 koleksiyonu (yalnızca değişkenler, gerçek kimlik bilgisi yok) |
| [`postman_smoke.py`](postman_smoke.py) | Koleksiyonu canlı sunucuya karşı sırayla çalıştıran küçük doğrulayıcı (Newman değildir) |
| [`screenshots/`](screenshots/) | Swagger UI'nin gerçek ekran görüntüleri |

## 1. Arayüzler

| URL | Açıklama |
|---|---|
| `/api/schema/` | OpenAPI şeması (varsayılan YAML; `?format=json` ile JSON) |
| `/api/docs/` | Swagger UI (statik dosyalar `drf-spectacular-sidecar` ile yerelden sunulur, CDN kullanılmaz) |
| `/api/redoc/` | ReDoc |

**Erişim politikası** (`API_DOCS_PUBLIC`, varsayılan = `DEBUG`): `true` iken üç adres de herkese açıktır;
`false` iken yalnızca personel (`is_staff`) kullanıcılar — yönetici oturumu veya JWT ile — erişebilir, diğerleri
401/403 alır. Bu ayar **yalnızca dokümantasyon adreslerini** etkiler; API'nin kimlik doğrulama ve izin
ayarları değiştirilmemiştir (korumalı uç noktalar her durumda 401 döner, testle doğrulanır).

Swagger UI'de `persistAuthorization` kapalıdır: girilen token tarayıcıya kaydedilmez, sayfa yenilenince silinir.

## 2. Uç nokta envanteri (21 işlem)

| Etiket | Yöntem | Yol | Kimlik | operationId |
|---|---|---|---|---|
| Kimlik Doğrulama | POST | `/api/auth/login/` | herkese açık | `auth_login` |
| Kimlik Doğrulama | POST | `/api/auth/refresh/` | herkese açık | `auth_refresh` |
| Kimlik Doğrulama | POST | `/api/auth/logout/` | JWT | `auth_logout` |
| Kimlik Doğrulama | GET | `/api/auth/me/` | JWT | `auth_me` |
| Parola İşlemleri | POST | `/api/auth/password-reset/` | herkese açık | `auth_password_reset_request` |
| Parola İşlemleri | POST | `/api/auth/password-reset/confirm/` | herkese açık | `auth_password_reset_confirm` |
| Proje Yükleme | POST | `/api/projects/` | JWT | `projects_create` |
| Proje Yönetimi | GET | `/api/projects/` | JWT | `projects_list` |
| Proje Yönetimi | GET | `/api/projects/{id}/` | JWT | `projects_retrieve` |
| Proje Yönetimi | PUT / PATCH | `/api/projects/{id}/` | JWT | `projects_update` / `projects_partial_update` |
| Proje Yönetimi | DELETE | `/api/projects/{id}/` | JWT | `projects_destroy` |
| Analiz İşlemleri | GET / POST | `/api/analysis-runs/` | JWT | `analysis_runs_list` / `analysis_runs_create` |
| Analiz İşlemleri | GET | `/api/analysis-runs/{id}/` | JWT | `analysis_runs_retrieve` |
| Referans Gereksinimler | GET / POST | `/api/reference-requirements/` | JWT | `reference_requirements_list` / `_create` |
| Referans Gereksinimler | GET / PUT / PATCH / DELETE | `/api/reference-requirements/{id}/` | JWT | `reference_requirements_retrieve` / `_update` / `_partial_update` / `_destroy` |

Envanterde olmayan yöntemler API'de de yoktur (ör. `DELETE /api/analysis-runs/{id}/` → 405); sözleşme testi
şemadaki işlem kümesinin bu tabloyla birebir aynı olduğunu doğrular.

**Sahiplik:** Tüm korumalı kaynaklar oturumdaki kullanıcıya göre süzülür. Başkasına ait bir kayıt **404** döner
(varlığı ifşa edilmez). Not: veri sözlüğü §13.1 bu durum için 403 öngörür; uygulama 404 döndürür ve şema
uygulamayı belgeler.

## 3. Hata biçimleri

| Durum | Gövde | Bileşen |
|---|---|---|
| 400 (alan doğrulama) | `{"<alan>": ["mesaj", ...], "non_field_errors": [...]}` | `ValidationError` |
| 400 (arşiv) | `{"archive": [{"code": "...", "detail": "...", "entries": [...]}]}` | `ArchiveError` |
| 401 (token yok) | `{"detail": "Giriş bilgileri verilmedi."}` | `DetailError` |
| 401 (geçersiz token) | `{"detail": "...", "code": "token_not_valid", "messages": [...]}` | `TokenError` |
| 404 / 405 / 409 / 413 / 415 / 429 | `{"detail": "..."}` | `DetailError` |

Şemadaki hata örnekleri gerçek isteklerin yanıtlarından alınmıştır ve sözleşme testinde gerçek yanıtlarla
birebir karşılaştırılır. 404 metni DRF'nin varsayılan İngilizce mesajıdır (`No Project matches the given query.`).

## 4. Şemayı yeniden üretme

Kodda serializer/görünüm değiştiğinde dışa aktarılan dosyalar güncellenmelidir (varsayılan yükleme sınırlarıyla):

```bash
cd backend
python manage.py spectacular --file ../docs/api/openapi.yaml --validate
python manage.py spectacular --format openapi-json --file ../docs/api/openapi.json --validate
```

`core/tests/test_openapi.py::test_committed_yaml_and_json_exports_are_current_and_equivalent` dosyalar eskiyse başarısız olur.

## 5. Uygulama notları

- Şema özelleştirmeleri `backend/core/api/schema.py` içindedir ve `OpenApiViewExtension` ile uygulanır; mevcut
  görünümlerin çalışma zamanı davranışı değiştirilmemiştir. Şema üretimi sırasında (`swagger_fake_view`) sahiplik
  süzgeci boş queryset döndürür, gerçek isteklerde etkisizdir.
- `ReferenceRequirement.specification` için `oneOf` (Role / AccessRule / DeployExpectation) ve salt-okunur
  `http_method` alanı `backend/core/serializers.py` içinde `extend_schema_field` ile tanımlanır.
- Enum adları `SPECTACULAR_SETTINGS["ENUM_NAME_OVERRIDES"]` ile sabitlenmiştir (`HttpMethodEnum` doğrudan
  `core.choices.HttpMethod`'dan türetilir).

## 6. Postman

Koleksiyonu içe aktarın, `baseUrl`, `username`, `password` değişkenlerini kendi ortamınızda doldurun. `Giriş` isteği
`accessToken`/`refreshToken` değişkenlerini, oluşturma istekleri `projectId`/`analysisRunId`/`requirementId`
değişkenlerini otomatik doldurur. `Proje oluştur` isteğinde `archive` alanı için yerel bir `.zip` seçin.

Komut satırından aynı akış (Postman/Newman yerine; yalnızca durum denetimi ve değişken aktarımı yorumlanır):

```bash
API_USERNAME=<kullanıcı> API_PASSWORD=<parola> python docs/api/postman_smoke.py --archive <proje.zip>
```

Doğrulama kaydı: [`backend/docs/evidence/h4_05_api_docs.md`](../../backend/docs/evidence/h4_05_api_docs.md).
