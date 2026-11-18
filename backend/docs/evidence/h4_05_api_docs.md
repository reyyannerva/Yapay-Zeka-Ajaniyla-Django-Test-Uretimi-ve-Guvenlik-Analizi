# H4-05 | Swagger / OpenAPI / Postman Dokümantasyonu — Kanıt (Issue #37)

Hafta 4 API'sinin (H4-02 #34, H4-03 #35, H4-04 #36) koddan üretilen OpenAPI 3.0.3 belgesi, Swagger UI/ReDoc,
kılavuzlar ve Postman koleksiyonu. Kılavuz: [`docs/api/README.md`](../../../docs/api/README.md).

## 1. Ön koşul

H4-01 (#33), H4-02 (#34), H4-03 (#35, PR #88) ve H4-04 (#36, PR #89) `main` dalında birleşmiştir
(`3e4a3a2`); `main`'e sonradan eklenen PR #90 (`generated_test_count`, `3af3b59`) bu dala birleştirilip şema yeniden üretilmiştir. Envanter, URL çözücüden ve görünüm sınıflarından çıkarılmıştır: 12 yol, 21 işlem.

## 2. Ortam

Django 5.2.19, DRF 3.18.3, SimpleJWT 5.5.1, django-axes 9.0.0, drf-spectacular 0.30.0,
drf-spectacular-sidecar 2026.10.1, PostgreSQL 16.15, Python 3.13.

## 3. Şema üretimi ve doğrulama

```text
$ python manage.py spectacular --file ../docs/api/openapi.yaml --validate
$ python manage.py spectacular --format openapi-json --file ../docs/api/openapi.json --validate
(uyarı/hata yok; YAML ve JSON içerik olarak eşit)
```

Üretici istatistiği (`GENERATOR_STATS`) uyarı ve hata içermez; bu bir testle (`test_schema_is_valid_openapi_and_generated_without_warnings`) korunur.

## 4. Sözleşme testleri — `core/tests/test_openapi.py` (51 test, PostgreSQL)

| Grup | Doğrulanan |
|---|---|
| Şema | OpenAPI 3.0 geçerliliği, uyarısız üretim, tekil operationId, tüm `$ref`'lerin çözülmesi |
| Envanter | Şemadaki (yol, yöntem) kümesi = beklenen 21 işlem; şemada olmayan yöntemler gerçekten 405 |
| Etiketler | 6 işlevsel etiket; her işlemde etiket, özet ve 2xx yanıt |
| Güvenlik | `jwtAuth` = http/bearer/JWT; genel `security` yok; herkese açık 4 işlem `security` içermez, diğer 17 işlem `jwtAuth` ister ve kimliksiz gerçek istekte **401** döner |
| Erişim politikası | `API_DOCS_PUBLIC=true` → şema/Swagger/ReDoc açık; `false` → anonim 401/403, normal kullanıcı 403, personel (JWT ve oturum) 200; API izinleri etkilenmez |
| Swagger UI | Statik dosyalar yerelden (CDN yok) |
| Yükleme | `multipart/form-data` tek içerik türü, `archive` = `string/binary`, zorunlular `name`+`archive` |
| İstek gövdeleri | Zorunlu alanlar gerçek serializer'larla eşit; salt-okunur alanlar istek bileşenlerinde yok (9 bileşen) |
| HTTP yöntemi | `HttpMethodEnum` = tam olarak GET/POST/PUT/PATCH/DELETE; gerçek API 5 yöntemi kabul, HEAD/OPTIONS/TRACE/`get`/boş değeri reddeder (10 parametre) |
| Durumlar | `AnalysisRunStatusEnum` = modeldeki 9 durum |
| Gerçek yanıtlar | Giriş, yenileme, me, proje oluştur/listele/güncelle, gereksinim oluştur/listele, analiz oluştur/listele/detay yanıtları JSON Schema ile bileşenlere karşı doğrulanır |
| Hata örnekleri | Şemadaki **31** hata örneği gerçek isteklerin gövdeleriyle birebir eşit (413 yalnızca yapı) |
| Kilit | 3 hatalı deneme → 401, 401, **429**; doğru parola ile de 429; `Retry-After` yok; gövde örnekle eşit |
| Örnekler | 2xx örnekleri ve istek örnekleri şemaya uygun; "400" örneği şemaya aykırı |
| Dışa aktarım | Depodaki YAML = JSON = yeni üretim |
| Gizlilik | Şema ve `docs/api` dosyalarında `SECRET_KEY`, veritabanı parolası, `BASE_DIR`, arşiv kökü, JWT benzeri değer, test parolası yok |
| Postman | v2.1 şeması, kimlik değişkenleri boş, her istek şemadaki bir işleme karşılık gelir, yükleme `formdata` + `file` |
| Belge örnekleri | Kılavuzdaki ROLE / DEPLOY_EXPECTATION / ACCESS_RULE örnekleri gerçek API'de 201 |

## 5. Regresyon (bu dalda, gerçek çıktı)

| Komut | Sonuç |
|---|---|
| `backend: python -m pytest` (PostgreSQL) | **428 passed** (377 önceki + 51 yeni) |
| `python manage.py check` | no issues |
| `python manage.py makemigrations --check --dry-run` | No changes detected |
| `python -m pytest agent` | 244 passed |
| `agent/test_generation/rule_based` | 132 passed |
| `agent/test_generation/llm` | 26 passed |
| `agent/evaluation` | 86 passed |
| `benchmarks/drf_fixtures/sample_app` | 69 passed |
| `benchmarks/reference_cases` | 48 passed |
| `experiments/h3_02_eda` | 67 passed |
| `python -m agent.evaluation verify` | Manifest geçerli (H3-06 sonuçları değişmedi) |

## 6. Swagger UI ve Postman akışı

`runserver` (PostgreSQL, `DEBUG=true`) üzerinde geçici bir kullanıcıyla doğrulanmıştır; kullanıcı ve verileri
sonra silinmiştir, parola rastgele üretilip hiçbir dosyaya yazılmamıştır.

**Postman koleksiyonu** — `docs/api/postman_smoke.py` ile (Postman/Newman **değildir**; yalnızca durum
denetimi ve değişken aktarımı yorumlanır):

```text
TAMAM    POST   {{baseUrl}}/api/auth/login/                             → 200
TAMAM    GET    {{baseUrl}}/api/auth/me/                                → 200
TAMAM    POST   {{baseUrl}}/api/auth/refresh/                           → 200
TAMAM    POST   {{baseUrl}}/api/auth/password-reset/                    → 200
ATLANDI  Yeni parola belirle
TAMAM    POST   {{baseUrl}}/api/projects/                               → 201
TAMAM    GET    {{baseUrl}}/api/projects/                               → 200
TAMAM    GET    {{baseUrl}}/api/projects/{{projectId}}/                 → 200
TAMAM    PATCH  {{baseUrl}}/api/projects/{{projectId}}/                 → 200
TAMAM    POST   {{baseUrl}}/api/analysis-runs/                          → 201
TAMAM    GET    {{baseUrl}}/api/analysis-runs/                          → 200
TAMAM    GET    {{baseUrl}}/api/analysis-runs/{{analysisRunId}}/        → 200
TAMAM    POST   {{baseUrl}}/api/reference-requirements/                 → 201
TAMAM    GET    {{baseUrl}}/api/reference-requirements/                 → 200
TAMAM    GET    {{baseUrl}}/api/reference-requirements/{{requirementId}}/ → 200
TAMAM    PATCH  {{baseUrl}}/api/reference-requirements/{{requirementId}}/ → 200
TAMAM    DELETE {{baseUrl}}/api/reference-requirements/{{requirementId}}/ → 204
TAMAM    DELETE {{baseUrl}}/api/projects/{{projectId}}/                 → 409
TAMAM    POST   {{baseUrl}}/api/auth/logout/                            → 205
```

`Yeni parola belirle` e-postadaki `uid`/`token` gerektirdiği için atlanmıştır (bu akış
`core/tests/test_auth_api.py` içinde doğrulanır). `DELETE /api/projects/{id}/` → 409 beklenen
davranıştır: proje `QUEUED` analiz içerir. Postman masaüstü uygulamasıyla elle çalıştırma **yapılmamıştır**.

**Ekran görüntüleri** (Playwright/Chromium, gerçek `/api/docs/`; Authorize penceresine token girilmemiştir):
`docs/api/screenshots/01-swagger-genel-bakis.png`, `02-authorize-jwt.png`, `03-proje-yukleme-multipart.png`,
`04-analiz-olusturma.png`, `05-referans-gereksinim.png`, `06-reference-specification-oneof.png`,
`07-analiz-durumlari.png`.

## 7. Güvenlik incelemesi

| Konu | Sonuç |
|---|---|
| API kimlik doğrulama/izinleri | Değiştirilmedi; dokümantasyon izni yalnızca `/api/schema/`, `/api/docs/`, `/api/redoc/` adreslerine uygulanır |
| Üretim varsayılanı | `API_DOCS_PUBLIC` varsayılanı `DEBUG`; `DEBUG=false` iken şema yalnızca personele açık |
| Token saklama | Swagger UI `persistAuthorization=false`; koleksiyonda token/parola değeri yok |
| Gizli değerler | Şema/dokümanlarda gizli anahtar, parola, gerçek JWT yok (testle) |
| Depolama yolu | `Project` yanıt şemasında depolama anahtarı/sunucu yolu yok; belgelerde arşiv kökü yok (testle) |
| Hesap varlığı ifşası | Şifre sıfırlama tek genel yanıtla belgelendi; giriş hatası kullanıcı adı/parola ayrımı yapmaz |
| Uydurma alanlar | 429 için `Retry-After`/`retry_after` iddia edilmedi (kilit yanıtında yok, testle) |
| Harici kaynak | Swagger UI/ReDoc dosyaları sidecar paketinden, CDN yok |
| Çalışma zamanı etkisi | Serializer değişiklikleri yalnızca şema ipuçlarıdır (`SpecificationField` = `JSONField(required=False)`, `HttpMethodReadField` = `CharField(read_only=True)`); görünümler değiştirilmedi, sahiplik süzgeci yalnızca şema üretiminde boş queryset döner |

## 8. Bulgular (düzeltilmedi, raporlandı)

1. **H4-04 — aktif analiz mesajı:** projede aktif analiz varken ikinci analiz oluşturma
   `{"non_field_errors": ["project  alanları benzersiz bir set yapmak gerekir."]}` döner. DRF'nin koşullu
   `UniqueConstraint`'ten ürettiği `UniqueTogetherValidator` özel mesajı gölgeler. Şema gerçek yanıtı belgeler.
2. **403 / 404:** veri sözlüğü §13.1 başkasına ait kayıt için 403 öngörür; uygulama 404 döndürür (varlık
   ifşa edilmez). Şema uygulamayı belgeler; belge ile kararın uzlaştırılması gerekir.
3. **404 metni İngilizce:** `No Project matches the given query.` (DRF varsayılanı).
