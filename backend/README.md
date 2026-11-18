# Backend — Django + PostgreSQL (H4-01 / Issue #33)

Bu dizin platformun Django backend'idir. H4-01 kapsamında **veri katmanı** kurulmuştur: PostgreSQL bağlantısı,
Django ORM modelleri, migration'lar, giriş kilidi verisi (django-axes) ve model/bütünlük testleri. API uç
noktaları, kimlik doğrulama akışları (H4-02 #34), proje/analiz API'leri (H4-03 #35, H4-04 #36) ve Celery işçileri
sonraki iş kalemleridir.

```text
backend/
├── manage.py
├── requirements.txt
├── .env.example          # ortam değişkeni şablonu (gerçek değer içermez)
├── pytest.ini
├── config/               # settings.py, env.py (ortam okuma), urls.py, wsgi.py, asgi.py
└── core/
    ├── models/           # 9 model (Project, ReferenceRequirement, AnalysisRun, Endpoint, GeneratedTest,
    │                     #          TestExecution, SecurityFinding, Report, LlmCall)
    ├── migrations/       # 0001_initial, 0002_project_archive_private_storage (H4-03)
    ├── auth/             # H4-02: SimpleJWT, kilit, şifre sıfırlama, sahiplik izinleri
    ├── projects/         # H4-03: proje API'si, arşiv güvenliği, Django yapı ön kontrolü
    ├── storage.py        # H4-03: herkese açık olmayan arşiv deposu
    ├── choices.py        # ortak HttpMethod (GET, POST, PUT, PATCH, DELETE)
    ├── fields.py         # NullableFileField
    ├── progress.py       # TestExecution kayıtlarından ilerleme türetme
    ├── serializers.py    # ReferenceRequirement / HTTP yöntemi doğrulama sözleşmesi
    ├── management/commands/check_database.py, cleanup_project_archives.py
    └── tests/            # PostgreSQL üzerinde model, kısıt, migration ve kilit testleri
```

Şema kararları ve değişiklik kaydı: [`docs/database/schema_changes_h4_01.md`](../docs/database/schema_changes_h4_01.md);
veri sözlüğü: [`docs/database/data_dictionary.md`](../docs/database/data_dictionary.md).

## 1. PostgreSQL kurulumu (yerel geliştirme)

PostgreSQL 14+ gerekir (doğrulama PostgreSQL 16.15 ile yapılmıştır). SQLite desteklenmez: şema kısmi tekil indeks,
JSONB anahtar kısıtları ve `DISTINCT ON` kullanır.

```bash
sudo -u postgres psql -c "CREATE ROLE ai_test_agent LOGIN PASSWORD '<güçlü-parola>' CREATEDB;"
```

```bash
sudo -u postgres psql -c "CREATE DATABASE ai_test_agent OWNER ai_test_agent ENCODING 'UTF8';"
```

`CREATEDB` yetkisi yalnızca testlerin geçici `test_<veritabanı>` veritabanını oluşturabilmesi içindir; üretim
rolüne verilmemelidir.

## 2. Ortam değişkenleri

```bash
cp backend/.env.example backend/.env
```

| Değişken | Zorunlu | Varsayılan | Açıklama |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | `DJANGO_DEBUG=false` iken evet | — | Yoksa ve DEBUG açıksa süreç başına geçici anahtar üretilir |
| `DJANGO_DEBUG` | Hayır | `false` | `true/false` |
| `DJANGO_ALLOWED_HOSTS` | Hayır | `localhost,127.0.0.1` | Virgülle ayrılmış |
| `POSTGRES_DB` | Evet | — | Veritabanı adı |
| `POSTGRES_USER` | Evet | — | Kullanıcı |
| `POSTGRES_PASSWORD` | Evet | — | Parola (varsayılan yoktur; hiçbir çıktıya yazılmaz) |
| `POSTGRES_HOST` | Hayır | `127.0.0.1` | Sunucu |
| `POSTGRES_PORT` | Hayır | `5432` | 1–65535 |
| `POSTGRES_CONNECT_TIMEOUT` | Hayır | `5` | Saniye |
| `POSTGRES_CONN_MAX_AGE` | Hayır | `0` | Kalıcı bağlantı süresi (sn) |
| `POSTGRES_TEST_DB` | Hayır | `test_<POSTGRES_DB>` | Test veritabanı adı |
| `PROJECT_ARCHIVE_ROOT` | Hayır | `backend/private_storage` | Yüklenen arşivlerin özel deposu (URL ile sunulmaz) |
| `PROJECT_UPLOAD_MAX_BYTES` ve diğer `PROJECT_UPLOAD_*` | Hayır | bkz. `docs/h4_03_project_api.md` §4 | Arşiv boyut, girdi, derinlik ve oran sınırları |

Değerler önce işletim sistemi ortamından, yoksa `backend/.env`'den okunur. `.env` git tarafından yok sayılır.
Eksik zorunlu değişkende hata iletisi yalnızca değişkenin **adını** verir.

## 3. Kurulum, bağlantı doğrulama ve migration

Depo kökünden:

```bash
pip install -r backend/requirements.txt
```

```bash
cd backend && python manage.py check_database
```

`check_database` sunucuya gerçekten bağlanıp `version()` sorgular; ayarların okunabilmesi bağlantı kanıtı sayılmaz.
Bağlantı kurulamazsa hedef (`kullanıcı@host:port/veritabanı`) ve PostgreSQL hatası yazılır, parola yazılmaz.

```bash
cd backend && python manage.py makemigrations --check --dry-run && python manage.py migrate && python manage.py check
```

```bash
cd backend && python manage.py showmigrations core axes
```

## 4. Testler

```bash
cd backend && python -m pytest -q
```

Testler pytest-django ile geçici bir PostgreSQL test veritabanında çalışır; geliştirme veritabanındaki veriye
dokunulmaz. Kapsam: yedi temel model (User + 6), destek tabloları, tüm CHECK/UNIQUE kısıtlarının veritabanı
düzeyinde reddi (`IntegrityError`, `full_clean()` yerine), HTTP yöntemi sözleşmesi (model + veritabanı +
serializer), durum ↔ zaman damgası kuralları, JSONB gidiş-dönüşü, silme davranışı, ilerleme türetme, django-axes
kilit verisi, migration tutarlılığı ve geri alma/yeniden uygulama.

## 5. Kapsam sınırları

* Giriş kilidi: 3 başarısız deneme → 15 dakika kilit **verisi** ve Django `authenticate()`/yönetici paneli giriş
  akışındaki django-axes davranışı kuruldu ve test edildi. DRF/SimpleJWT giriş API'si ve yanıtları H4-02 (#34)
  kapsamında eklendi (bkz. §6).
* AnalysisRun durum geçiş servisi, Celery görevleri ve kalan süre tahmini kapsam dışıdır; veri yapıları hazırdır.

## 6. Kimlik doğrulama ve yetkilendirme (H4-02 / Issue #34)

SimpleJWT giriş/yenileme/çıkış (django-axes kilidine entegre), e-posta ile şifre sıfırlama ve proje
sahipliği bazlı DRF izinleri `/api/auth/` altında eklenmiştir. Uç noktalar, yapılandırma ve örnek
istek–yanıtlar: [`docs/evidence/h4_02_auth_api.md`](docs/evidence/h4_02_auth_api.md). Kaynak: `core/auth/`.
Testler: `core/tests/test_auth_api.py`, `core/tests/test_permissions.py`.

SimpleJWT bağımlılığı `requirements.txt`'e eklendi; `pip install -r backend/requirements.txt` sonrası
`python manage.py migrate` (token_blacklist migration'ları dâhil) çalıştırılmalıdır.

## 7. Proje yönetimi ve arşiv yükleme (H4-03 / Issue #35)

`/api/projects/` altında proje oluşturma (multipart ZIP yükleme), listeleme, detay, güncelleme ve silme
uç noktaları vardır. Tüm uç noktalar SimpleJWT ister. Kullanıcılar yalnızca kendi projelerini görür;
başkasının projesi 404 döner. Yüklenen kod çalıştırılmaz, içe aktarılmaz ve diske açılmaz.

Uç noktalar, sınırlar, arşiv güvenlik denetimleri, depolama ve silme davranışı:
[`docs/h4_03_project_api.md`](docs/h4_03_project_api.md). Gerçek istek-yanıtlar ve PostgreSQL kaydı:
[`docs/evidence/h4_03_project_api.md`](docs/evidence/h4_03_project_api.md). Kaynak: `core/projects/`,
`core/storage.py`. Testler: `core/tests/test_project_api.py`, `core/tests/test_project_archive.py`.

Yeni migration `core.0002_project_archive_private_storage` yalnızca depolama arka ucunu kaydeder; veritabanında
değişiklik yapmaz (`python manage.py migrate` ile uygulanır).

## 8. Analiz ve referans gereksinim API'leri (H4-04 / Issue #36)

`/api/analysis-runs/` (oluşturma `QUEUED` + listeleme + detay/ilerleme) ve `/api/reference-requirements/`
(kaynak koddan bağımsız referans JSON CRUD; `specification.method` yalnızca GET/POST/PUT/PATCH/DELETE).
Sahiplik H4-02 (#34) izinleriyle; referans doğrulaması H4-01 (#33) serializer'ıyla; ilerleme
`core/progress.py` ile. Bu aşamada gerçek AST/LLM/Docker başlatılmaz. Uç noktalar + örnek istek-yanıtlar:
[`docs/evidence/h4_04_analysis_reference_api.md`](docs/evidence/h4_04_analysis_reference_api.md).
Kaynak: `core/api/`. Testler: `core/tests/test_analysis_api.py`, `core/tests/test_requirement_api.py`.

## 9. API dokümantasyonu — Swagger / OpenAPI (H4-05 / Issue #37)

Şema `drf-spectacular` ile koddan üretilir: `/api/schema/` (OpenAPI 3.0.3), `/api/docs/` (Swagger UI, yerel
statik dosyalar), `/api/redoc/`. Erişim `API_DOCS_PUBLIC` ile denetlenir (varsayılan `DEBUG`; `false` iken
yalnızca `is_staff`). Dışa aktarılmış şema, kılavuzlar ve Postman koleksiyonu:
[`../docs/api/`](../docs/api/README.md). Şema özelleştirmeleri: `core/api/schema.py`. Sözleşme testleri:
`core/tests/test_openapi.py`. Doğrulama kaydı: [`docs/evidence/h4_05_api_docs.md`](docs/evidence/h4_05_api_docs.md).
