# H4-01 (Issue #33) — Şemanın Django ORM ile Uygulanması: Kararlar, Eşleme ve Değişiklik Kaydı

| Bilgi | Değer |
|---|---|
| İş kalemi | H4-01 / #33 — Veritabanı Modelleri ve Migration Altyapısının Oluşturulması |
| Temel alınan tasarım | `docs/database/` revizyon 3 (`9a4324b`, kanonik; PR #82) |
| Sonuç | Revizyon 4 — `backend/core/models/`, migration `backend/core/migrations/0001_initial.py` |
| Doğrulama ortamı | PostgreSQL 16.15, Django 5.2.19, DRF 3.18.3, django-axes 9.0.0, psycopg 3.3.9, Python 3.13.18 |

## 1. Kanonik tasarımın doğrulanması

İncelenen kaynaklar: `database_schema.sql`, `django_models.py` (rev. 3), `data_dictionary.md`,
`schema_validation.md`, `docs/diagrams/er-diagrams/*`, `docs/architecture/technology_stack.md`, Issue #24, #26, #33,
#34 ve PR #82. Revizyon 3'ün kanonik olduğu `docs/database/README.md`'de gerekçelendirilmiştir; bu belgeler kendi
içinde tutarlıdır (9 tablo, 122 sütun, 13 FK, 11 JSONB sütunu, 85 adlandırılmış kısıt/indeks).

Kanonik varlıklar (`schema_validation.md` A): **User** (`auth_user`, Django), Project, ReferenceRequirement,
AnalysisRun, Endpoint, GeneratedTest, TestExecution, SecurityFinding, Report, LlmCall ve çerçeve yönetimli
django-axes tabloları.

## 2. Yedi temel model ile dokuz tablonun uzlaştırılması

Issue #33 "yedi temel Django ORM modeli" ister ve altısını adlandırır (Project, AnalysisRun, ReferenceRequirement,
GeneratedTest, TestExecution, SecurityFinding). İlk maddesi aynı cümlede **kullanıcı modeli stratejisini** ister.
Yedinci model kanonik şemadan şöyle belirlenmiştir:

* Revizyon 1 tasarımı (`728547c`, Issue #24 ile aynı gün) tam olarak **User + 6 tablodan** oluşur; Issue #33 bu
  tasarıma göre yazılmıştır.
* `schema_validation.md` A tablosunda varlık 1 **User** (`auth_user`, `settings.AUTH_USER_MODEL`) olarak yer alır
  ve altı adlandırılmış tabloyla tek ilişkisi R1 (User → Project) zorunlu sahipliktir.

**Yedinci temel model = User (`django.contrib.auth.User`, `settings.AUTH_USER_MODEL`).** Özel bir model
tanımlanmaz (bkz. §3).

Revizyon 3'ün ek tabloları **atılmamış**, kanonik şemaya uymak için uygulanmıştır:

| Tablo | Sınıf | Neden bu issue'da |
|---|---|---|
| `endpoints` | Destek tablosu | `generated_tests.endpoint_id` ve `security_findings.endpoint_id` FK'leri bu tabloya bağlıdır; atılırsa iki temel tablo kanonik şemadan ayrışır. |
| `reports` | Destek tablosu (gelecek iş: rapor üretimi H6) | Kanonik şemanın parçası; şimdi oluşturmak ikinci bir şema dalı açılmasını önler. Yalnızca tablo ve kısıtlar; rapor üretimi yok. |
| `llm_calls` | Destek tablosu (gelecek iş: LiteLLM entegrasyonu) | Aynı gerekçe; İST-13 token metrikleri. Yalnızca tablo ve kısıtlar. |

## 3. Kimlik doğrulama modeli stratejisi

**Karar: Django'nun yerleşik `auth.User` modeli** (`AUTH_USER_MODEL = "auth.User"`), tüm ilişkiler
`settings.AUTH_USER_MODEL` üzerinden.

Gerekçe:

1. Veri sözlüğü K1: hesaplar yönetici panelinden açılır; kayıt ekranı yoktur; kullanıcı adı + e-posta + parola
   özeti `auth_user`'da yeterlidir. Ek profil alanı gerektiren bir ister yoktur.
2. Şifre sıfırlama Django'nun `PasswordResetTokenGenerator`'ını kullanır; belirteç saklanmaz, tablo gerekmez.
3. Issue #33 "kullanıcı modelini gereksiz yere değiştirmeden" ister.
4. Özel model, ilk migration'dan sonra değiştirilmesi zor bir karardır; ihtiyaç yokken eklenmesi geri dönüşü
   zor bir karmaşıklık getirir.

Migration etkisi: `core.0001_initial`, `auth` migration'larına bağımlıdır (`migrations.swappable_dependency`);
`projects.owner_id` → `auth_user.id` (integer, `auth` uygulaması `AutoField` kullanır). İleride özel modele geçmek
gerekirse bu, ayrı bir veri taşıma çalışması gerektirir ve bu belgeye kaydedilmelidir.

### Giriş denemesi ve geçici kilit verisi (3 başarısız deneme → 15 dakika)

Kanonik tasarım ve teknoloji yığını django-axes'i öngörür (`technology_stack.md`, sözlük 4.11). Kullanıcı tablosu
değiştirilmeden kalıcı veri django-axes tablolarında tutulur:

| Bilgi | Tablo.sütun |
|---|---|
| Başarısız deneme sayısı | `axes_accessattempt.failures_since_start` (kullanıcı adı bazında) |
| Son deneme zamanı | `axes_accessattempt.attempt_time` |
| Kilit bitiş zamanı | `axes_accessattemptexpiration.expires_at` (`AXES_USE_ATTEMPT_EXPIRATION = True`) |
| Her başarısız denemenin kaydı, kilit bayrağı | `axes_accessfailurelog` (`locked_out`) |

Ayarlar (`backend/config/settings.py`): `AXES_FAILURE_LIMIT = 3`, `AXES_COOLOFF_TIME = 15 dk`,
`AXES_LOCKOUT_PARAMETERS = ["username"]`, `AXES_RESET_ON_SUCCESS = True`. `axes.W006` uyarısı bilinçli olarak
susturulmuştur: ister hesap bazlı kilittir; IP bazlı istek sınırlaması #34'ün kapsamındadır.

Kapsam sınırı: Bu issue **kalıcı veri yapısını** ve Django `authenticate()` / yönetici paneli giriş akışındaki
django-axes davranışını kurar ve test eder (3. denemede kilit, kilitliyken doğru parolanın reddi, başarılı girişte
sayacın sıfırlanması). DRF/SimpleJWT giriş uç noktaları, API hata yanıtları ve eşzamanlı istek senaryoları
**H4-02 (#34)** kapsamındadır. Parola, sıfırlama belirteci veya JWT hiçbir uygulama tablosunda saklanmaz.

## 4. Model ↔ şema eşlemesi

Gerçek veritabanında karşılaştırma: `database_schema.sql` boş bir PostgreSQL veritabanına uygulanmış ve
migration ile oluşturulan şemayla `information_schema` / `pg_constraint` üzerinden karşılaştırılmıştır:

* 9 tablo, **122 sütun**: ad, tip, uzunluk ve NULL olabilirlik **birebir aynı**;
* **87** adlandırılmış CHECK / UNIQUE / indeks: ad kümesi **birebir aynı** (revizyon 3: 85; +2 yeni kısıt).

| Model | Tablo | Sütun | Sınıflandırma |
|---|---|---|---|
| `auth.User` | `auth_user` | Django | Tam eşleşme (çerçeve yönetimli) |
| `Project` | `projects` | 12 | Tam eşleşme; `source_archive` için `NullableFileField` (§5, D3) |
| `ReferenceRequirement` | `reference_requirements` | 13 | Tam eşleşme + issue kaynaklı kısıt (§5, D2) |
| `AnalysisRun` | `analysis_runs` | 18 | Tam eşleşme (Issue #33 durumları, `celery_task_id`, zaman damgaları, 3 JSONField mevcut) |
| `Endpoint` | `endpoints` | 10 | Tam eşleşme |
| `GeneratedTest` | `generated_tests` | 18 | Tam eşleşme |
| `TestExecution` | `test_executions` | 14 | Sütunlar tam eşleşme; durum değer kümesi issue kaynaklı değişiklik (§5, D1) |
| `SecurityFinding` | `security_findings` | 17 | Tam eşleşme |
| `Report` | `reports` | 8 | Tam eşleşme |
| `LlmCall` | `llm_calls` | 12 | Tam eşleşme |

Tüm alan adları, `related_name`, `on_delete` (CASCADE / SET_NULL), `db_index=False` + kapsayan indeks kararları ve
`db_table` adları revizyon 3 ile aynıdır. Değer kümeleri tek kaynaktan (`TextChoices`) türetilir; CHECK kısıtları
ile `choices` aynı listeyi kullanır (`core/choices.py::values`).

## 5. Değişiklik kaydı (revizyon 3 → 4)

| No | Özgün tasarım | Yeni uygulama | Neden | İlgili Issue #33 maddesi | Migration etkisi | Sınıf |
|---|---|---|---|---|---|---|
| D1 | `test_executions.status` ∈ {QUEUED, RUNNING, PASS, FAIL, TECHNICAL_ERROR, STOPPED, NOT_RUN}; varsayılan QUEUED; zaman aşımı = TECHNICAL_ERROR + `error_type = TIMEOUT` | ∈ {**PENDING**, RUNNING, PASS, FAIL, **ERROR**, **TIMEOUT**, STOPPED, NOT_RUN}; varsayılan PENDING. Kısıtlar: `ck_test_executions_error_has_type` (ERROR'da tür zorunlu, TIMEOUT değil), yeni `ck_test_executions_timeout_consistent`, `ck_test_executions_pending_not_started`; `outcome_requires_start` TIMEOUT'u, `terminal_finished` ERROR/TIMEOUT'u kapsar | Issue #33 bu altı durumu adıyla ister ve "mevcut şemayla karşılaştırarak tamamlamayı" söyler. Eş anlamlı iki değer (QUEUED/PENDING) tutmak yerine yeniden adlandırıldı; iptal ekranı (Figma 29) için STOPPED / NOT_RUN korundu | "TestExecution kayıtlarında her testin durumunu (PENDING, RUNNING, PASS, FAIL, ERROR, TIMEOUT)…" | İlk migration; veri taşıması yok (önceden uygulanmış şema yok) | Issue kaynaklı değişiklik |
| D2 | `ACCESS_RULE` yöntemi yalnızca uygulama katmanında doğrulanacaktı ("veritabanı JSON içeriğini denetlemez") | Yeni `ck_reference_requirements_access_rule_method`: `specification ? 'method'` ve değer ∈ {GET, POST, PUT, PATCH, DELETE}; ayrıca `ReferenceRequirement.clean()` ve `core/serializers.py` sözleşmesi | Issue #33 "izin verilen metot değerlerini doğrulayan model/serializer sözleşmesi" ister; `choices` tek başına veritabanında zorlanmaz. Yöntem kanonik tasarımdaki gibi `specification` JSON'unda kalır (bir gereksinim = bir endpoint + bir yöntem) | "ReferenceRequirement verilerinde GET, POST, PUT, PATCH ve DELETE…" | Yeni CHECK; ek sütun yok | Issue kaynaklı ek |
| D3 | `projects.source_archive`: `FileField(null=True)`; dizin projelerinde `NULL` (CHECK ile) | `NullableFileField` (`core/fields.py`): boş dosyayı `''` değil `NULL` yazar | Django `FileField` `null=True` olsa bile boş değeri `''` saklar; bu, kanonik `ck_projects_directory_source_present` kısıtını ihlal eder (test sırasında `IntegrityError` ile bulundu). Revizyon 3 modelleri hiç çalıştırılmadığı için görünmemişti | Model ve kısıtların tasarımla uyumu | Sütun tipi aynı (`varchar(255)`); yalnızca ORM yazma davranışı | Mevcut tasarım tutarsızlığı |
| D4 | `AnalysisRun.status` 9 değer | Değişmedi. Issue #33'ün 6 değeri birebir var; VALIDATING, SCANNING, CANCELLED revizyon 3'te Figma ekranları için eklenmiş ve korunmuştur | Kaldırmak revizyon 3'ün Figma'ya dayanan doğrulama/tarama aşamalarını ve iptal akışını (ekran 28, 29) bozardı | "QUEUED, ANALYZING, GENERATING, EXECUTING, COMPLETED, FAILED durumlarını… eklemek" | Yok | Tam eşleşme (üst küme) |
| D5 | Giriş kilidi: django-axes (sürüm belirsiz, 9.0.0 incelendi) | django-axes **9.0.0** sabitlendi; `AXES_USE_ATTEMPT_EXPIRATION = True` ile `axes_accessattemptexpiration` kullanılır | Kilit bitiş zamanının kalıcı tutulması (Issue #33) | "başarısız deneme sayısı ve kilit bitiş zamanı…" | axes 0001–0010 migration'ları | Tam eşleşme |
| D6 | `django_models.py` çalışmayan referans | `backend/core/models/` (paket); `docs/database/django_models.py` yönlendirme notu | İki model tanımının ayrışmasını önlemek | "Model kodlarını… GitHub reposuna eklemek" | — | Belge düzeni |

## 6. AnalysisRun durumları ve Celery

* `TextChoices` + `ck_analysis_runs_status_valid`; varsayılan `QUEUED`.
* `celery_task_id` `NULL` olabilir (görev gönderilmeden önce), doluyken tekil (`uq_analysis_runs_celery_task_id`).
* Zaman damgaları: `created_at`, `started_at`, `finished_at`, `updated_at`; durum ↔ zaman tutarlılığı 5 CHECK ile
  (QUEUED başlamamış, ilerleyen durumlar başlamış, bitiş yalnızca ve her zaman uç durumlarda, sıra, FAILED'da hata
  kodu).
* JSONField: `requirements_snapshot` (liste), `ast_results`, `processing_metadata` (nesne).
* Projede tek aktif çalıştırma: kısmi tekil indeks `uq_analysis_runs_one_active_per_project`.
* Celery işçisi / görev orkestrasyonu bu issue'da **yoktur**. Durum geçiş sırası (8.2) veritabanında zorlanamaz;
  ileride tek bir servis fonksiyonu koşullu `UPDATE … WHERE status = <beklenen>` veya `select_for_update()` ile
  uygulamalıdır (sözlük 8.3).

## 7. TestExecution, ilerleme ve kalan süre verisi

* Test bazında durum, `started_at`, `finished_at`, `duration_ms`, `observed_status`, `output_excerpt`,
  `error_summary`, `error_type`, `error_origin`, `result_details` saklanır. Analiz çalıştırması
  `generated_test → analysis_run` zinciriyle türetilir (doğrudan FK yok; sözlük 6.2).
* İlerleme sayaçları **saklanmaz**, `core/progress.py::execution_progress()` ile türetilir (her testin en yüksek
  `attempt_number`'lı denemesi; tamamlanan = PASS, FAIL, ERROR, TIMEOUT, STOPPED, NOT_RUN). Gerekçe: eşzamanlı
  biten denemelerde değiştirilebilir sayaçlar kilit gerektirir ve sapabilir.
* Kalan süre tahmini için veri: tamamlanan denemelerin `duration_ms` toplamı ve sayısı, bekleyen/çalışan sayısı,
  `analysis_runs.started_at`. Tahmin algoritması kapsam dışıdır.
* Sorgu `DISTINCT ON (generated_test_id)` kullanır (PostgreSQL'e özgü). `uq_test_executions_test_attempt` indeksi
  `(generated_test_id, attempt_number)` sırasını kapsar.

## 8. Eşzamanlılık değerlendirmesi

| Risk | Bu revizyondaki koruma | İleride gereken |
|---|---|---|
| Aynı projede iki aktif analiz | Kısmi tekil indeks (yarışta ikinci `INSERT` `IntegrityError` alır) | Servis katmanında `IntegrityError` → 409 eşlemesi |
| Aynı Celery görevinin iki kez bağlanması | `uq_analysis_runs_celery_task_id` | — |
| Durum geçiş yarışı | Satır içi CHECK'ler | Koşullu `UPDATE` veya `select_for_update()` (sözlük 8.2–8.5) |
| Aynı test için eşzamanlı yeniden deneme | `uq_test_executions_test_attempt` | Yeni `attempt_number` için `select_for_update()` veya tekrar deneme |
| Aynı testin iki kez kaydedilmesi | `uq_generated_tests_run_module_name` | Üretici `get_or_create` / çakışmada güncelleme |
| Aynı bulgunun yinelenmesi | `uq_security_findings_run_fingerprint` | `ON CONFLICT DO NOTHING` eşdeğeri |
| Eşzamanlı giriş denemeleri | django-axes satır güncellemesi | #34: sayaç ve kilit tutarlılığı testleri |

## 9. Migration mimarisi

* Tek uygulama (`core`), tek başlangıç migration'ı `0001_initial` (9 model, 70 CHECK, 7 UNIQUE, kısmi tekil
  indeks, 9 indeks). Bağımlılık: `auth` (swappable). Paylaşılan bir ortama uygulanmadan önce üretildiği için
  geliştirme sırasında yeniden üretilmiştir; **bu PR'dan sonra uygulanmış migration'lar düzenlenmez**, değişiklikler
  yeni migration'larla yapılır.
* `makemigrations --check --dry-run` → "No changes detected"; `migrate` iki kez çalıştırıldığında ikincisi
  "No migrations to apply"; `migrate core zero` → `migrate core` döngüsü test edilmiştir
  (`test_core_migrations_roll_back_and_reapply_cleanly`).
* Üretilen DDL: `migrations_sql/0001_initial.postgresql.sql`.
* FK'ler Django'nun PostgreSQL davranışıyla `DEFERRABLE INITIALLY DEFERRED`, `ON DELETE` eylemi olmadan oluşturulur;
  silme davranışı ORM'dedir (sözlük 12).

## 10. Kanıt

Ham komut çıktıları: `backend/docs/evidence/h4_01_migration_evidence.md`. Testler:
`backend/core/tests/` (PostgreSQL test veritabanında).
