# Şema Doğrulama ve ER Diyagramı Sözleşmesi — H2-02 / Issue #24 (Revizyon 2)

Bu belge, `database_schema.sql`, `django_models.py` ve `data_dictionary.md` dosyalarının birbiriyle, Issue #24 kabul ölçütleriyle ve Figma mockup'ıyla (`docs/mockup/README.md`) tutarlılığını gösteren teknik inceleme ve devir belgesidir. ER diyagramı bu belgenin E bölümüne göre çizilir ve onunla karşılaştırılır. Revizyon 2'de yapılan değişikliklerin listesi ve mockup karşılıkları I bölümündedir.

---

## A. Varlık Kapsamı

| No | Mantıksal varlık | Tablo | Django modeli | Tanımlandığı yer | Durum |
|---|---|---|---|---|---|
| 1 | User | `auth_user` | `settings.AUTH_USER_MODEL` | Django `django.contrib.auth` | Çerçeve tarafından yönetilir; bu pakette yeniden tanımlanmaz. Sahiplik ilişkisi ve PK tipi veri sözlüğü 4.1'de. |
| 2 | Project | `projects` | `Project` | SQL bölüm 1, ORM, sözlük 4.2 | Tanımlı |
| 3 | ReferenceRequirement | `reference_requirements` | `ReferenceRequirement` | SQL bölüm 2, ORM, sözlük 4.3 | Tanımlı |
| 4 | AnalysisRun | `analysis_runs` | `AnalysisRun` | SQL bölüm 3, ORM, sözlük 4.4 | Tanımlı |
| 5 | Endpoint | `endpoints` | `Endpoint` | SQL bölüm 4, ORM, sözlük 4.8 | Tanımlı |
| 6 | GeneratedTest | `generated_tests` | `GeneratedTest` | SQL bölüm 5, ORM, sözlük 4.5 | Tanımlı |
| 7 | TestExecution | `test_executions` | `TestExecution` | SQL bölüm 6, ORM, sözlük 4.6 | Tanımlı |
| 8 | SecurityFinding | `security_findings` | `SecurityFinding` | SQL bölüm 7, ORM, sözlük 4.7 | Tanımlı |
| 9 | Report | `reports` | `Report` | SQL bölüm 8, ORM, sözlük 4.9 | Tanımlı |
| 10 | LlmCall | `llm_calls` | `LlmCall` | SQL bölüm 9, ORM, sözlük 4.10 | Tanımlı |
| — | Giriş kilidi | `axes_accessattempt`, `axes_accesslog`, `axes_accessfailurelog`, `axes_accessattemptexpiration` | django-axes modelleri | django-axes migration'ları | Çerçeve tarafından yönetilir; sözlük 4.11'de tanıtılır, FK'si yoktur. |

Uygulamanın sahip olduğu 9 tablo dışında tablo tanımlanmamıştır. Proje üyeliği veya paylaşım tablosu yoktur. Gereksinim sürümlemesi ek tablo yerine `reference_requirements.revision` ve `analysis_runs.requirements_snapshot` ile çözülmüştür. Şifre sıfırlama Django'nun belirteç mekanizmasını kullanır ve tablo gerektirmez.

## B. İlişki Matrisi

| No | Üst | Alt | FK sütunu → hedef | Çokluk | Alt FK NULL olabilir mi | Django `on_delete` | PostgreSQL FK davranışı | FK'yi kapsayan indeks |
|---|---|---|---|---|---|---|---|---|
| R1 | User | Project | `projects.owner_id → auth_user.id` | 1 : 0..N | Hayır | CASCADE | NO ACTION, DEFERRABLE INITIALLY DEFERRED | uq_projects_owner_name |
| R2 | Project | ReferenceRequirement | `reference_requirements.project_id → projects.id` | 1 : 0..N | Hayır | CASCADE | NO ACTION, DEFERRABLE INITIALLY DEFERRED | uq_reference_requirements_project_code |
| R3 | Project | AnalysisRun | `analysis_runs.project_id → projects.id` | 1 : 0..N | Hayır | CASCADE | NO ACTION, DEFERRABLE INITIALLY DEFERRED | ix_analysisrun_project_created |
| R4 | AnalysisRun | Endpoint | `endpoints.analysis_run_id → analysis_runs.id` | 1 : 0..N | Hayır | CASCADE | NO ACTION, DEFERRABLE INITIALLY DEFERRED | uq_endpoints_run_path_method |
| R5 | AnalysisRun | GeneratedTest | `generated_tests.analysis_run_id → analysis_runs.id` | 1 : 0..N | Hayır | CASCADE | NO ACTION, DEFERRABLE INITIALLY DEFERRED | uq_generated_tests_run_module_name |
| R6 | Endpoint | GeneratedTest | `generated_tests.endpoint_id → endpoints.id` | 0..1 : 0..N | Evet | SET_NULL | NO ACTION, DEFERRABLE INITIALLY DEFERRED | ix_gentest_endpoint |
| R7 | GeneratedTest | TestExecution | `test_executions.generated_test_id → generated_tests.id` | 1 : 0..N | Hayır | CASCADE | NO ACTION, DEFERRABLE INITIALLY DEFERRED | uq_test_executions_test_attempt |
| R8 | AnalysisRun | SecurityFinding | `security_findings.analysis_run_id → analysis_runs.id` | 1 : 0..N | Hayır | CASCADE | NO ACTION, DEFERRABLE INITIALLY DEFERRED | uq_security_findings_run_fingerprint, ix_finding_run_severity |
| R9 | TestExecution | SecurityFinding | `security_findings.test_execution_id → test_executions.id` | 0..1 : 0..N | Evet | SET_NULL | NO ACTION, DEFERRABLE INITIALLY DEFERRED | ix_finding_execution |
| R10 | Endpoint | SecurityFinding | `security_findings.endpoint_id → endpoints.id` | 0..1 : 0..N | Evet | SET_NULL | NO ACTION, DEFERRABLE INITIALLY DEFERRED | ix_finding_endpoint |
| R11 | AnalysisRun | Report | `reports.analysis_run_id → analysis_runs.id` | 1 : 0..N | Hayır | CASCADE | NO ACTION, DEFERRABLE INITIALLY DEFERRED | ix_report_run_created |
| R12 | AnalysisRun | LlmCall | `llm_calls.analysis_run_id → analysis_runs.id` | 1 : 0..N | Hayır | CASCADE | NO ACTION, DEFERRABLE INITIALLY DEFERRED | ix_llmcall_run_created |
| R13 | GeneratedTest | LlmCall | `llm_calls.generated_test_id → generated_tests.id` | 0..1 : 0..N | Evet | SET_NULL | NO ACTION, DEFERRABLE INITIALLY DEFERRED | ix_llmcall_generated_test |

Silme davranışı: zincirleme silme ve `SET_NULL` Django ORM tarafından yapılır; veritabanı, alt kaydı veya başvurusu bulunan üst kaydın ham SQL ile silinmesini commit anında reddeder (veri sözlüğü 12.1, 14.2 F3). Proje silindiğinde rapor ve arşiv dosyaları uygulama tarafından depodan silinir.

TestExecution ile AnalysisRun arasında doğrudan yabancı anahtar yoktur. İlişki yalnızca `test_executions → generated_tests → analysis_runs → projects` zinciriyle kurulur. İsteğe bağlı çapraz başvurularda (R6, R9, R10, R13) bağlanan kaydın aynı çalıştırmaya ait olması uygulama katmanında denetlenir (sözlük 6.4, 7.2/9).

## C. SQL–ORM Tutarlılık Matrisi

### C.1 Tablo ve sütun düzeyi

| Tablo (`db_table`) | Model | Sütun sayısı (SQL / ORM / sözlük) | PK | Kontrollü değerler (CHECK ↔ TextChoices) | JSONB ↔ JSONField | Zaman damgaları |
|---|---|---|---|---|---|---|
| projects | Project | 12 / 12 / 12 | bigint identity ↔ BigAutoField | source_type: ARCHIVE, ALLOWED_DIRECTORY; validation_status: PENDING, VALID, INVALID | validation_report | created_at, updated_at |
| reference_requirements | ReferenceRequirement | 13 / 13 / 13 | bigint identity ↔ BigAutoField | category: ROLE, ACCESS_RULE, DEPLOY_EXPECTATION; source: FORM, JSON_UPLOAD | specification | created_at, updated_at |
| analysis_runs | AnalysisRun | 18 / 18 / 18 | bigint identity ↔ BigAutoField | status: QUEUED, ANALYZING, GENERATING, VALIDATING, EXECUTING, SCANNING, COMPLETED, FAILED, CANCELLED; method: RULE_BASED, DIRECT_LLM, HYBRID; llm_provider: GROQ, GEMINI, OLLAMA | requirements_snapshot, ast_results, processing_metadata | created_at, started_at, finished_at, updated_at |
| endpoints | Endpoint | 10 / 10 / 10 | bigint identity ↔ BigAutoField | http_method: GET, POST, PUT, PATCH, DELETE; unsupported_reason: DYNAMIC_ROUTE, CUSTOM_PERMISSION | permission_classes | created_at |
| generated_tests | GeneratedTest | 18 / 18 / 18 | bigint identity ↔ BigAutoField | generation_method: LLM, RULE_BASED; validation_status: PENDING, VALID, INVALID_SYNTAX, REJECTED_POLICY | validation_errors, generation_metadata | created_at, updated_at |
| test_executions | TestExecution | 14 / 14 / 14 | bigint identity ↔ BigAutoField | status: QUEUED, RUNNING, PASS, FAIL, TECHNICAL_ERROR, STOPPED, NOT_RUN; error_type: IMPORT, FIXTURE, SYNTAX, TIMEOUT, OOM, OTHER; error_origin: TEST_CODE, TARGET_APP, INFRASTRUCTURE | result_details | started_at, finished_at, created_at |
| security_findings | SecurityFinding | 17 / 17 / 17 | bigint identity ↔ BigAutoField | source: AUTH_TEST, BANDIT, CHECK_DEPLOY; severity: HIGH, MEDIUM, LOW, UNKNOWN; classification: VERIFIED, POSSIBLE, UNCERTAIN | details | created_at |
| reports | Report | 8 / 8 / 8 | bigint identity ↔ BigAutoField | format: PDF, JSON; scope: FULL, PARTIAL | sections | created_at |
| llm_calls | LlmCall | 12 / 12 / 12 | bigint identity ↔ BigAutoField | provider: GROQ, GEMINI, OLLAMA; purpose: GENERATE, REPAIR; status: SUCCESS, ERROR, QUOTA_EXCEEDED, TIMEOUT | — | created_at |

Toplam 122 sütun, 11 JSONB sütunu. Her sütunun adı, sırası, tipi, `NULL` durumu ve `varchar` uzunluğu; SQL kataloğu, SQL metni, ORM tanımı ve veri sözlüğü arasında otomatik olarak karşılaştırılmıştır (H bölümü).

### C.2 Adlandırılmış kısıt ve indeksler

| Tablo | Tekil kısıt / tekil indeks | CHECK kısıtları | Açık indeksler |
|---|---|---|---|
| projects | uq_projects_owner_name | ck_projects_archive_sha256_format, ck_projects_archive_source_present, ck_projects_directory_source_present, ck_projects_name_not_blank, ck_projects_source_archive_relative, ck_projects_source_directory_relative, ck_projects_source_type_valid, ck_projects_validation_status_valid | — |
| reference_requirements | uq_reference_requirements_project_code | ck_reference_requirements_category_valid, ck_reference_requirements_code_format, ck_reference_requirements_expected_result_not_blank, ck_reference_requirements_revision_positive, ck_reference_requirements_source_valid, ck_reference_requirements_title_not_blank | — |
| analysis_runs | uq_analysis_runs_celery_task_id, uq_analysis_runs_one_active_per_project (kısmi) | ck_analysis_runs_coverage_range, ck_analysis_runs_failure_has_error_code, ck_analysis_runs_finished_iff_terminal, ck_analysis_runs_llm_provider_valid, ck_analysis_runs_llm_settings, ck_analysis_runs_method_valid, ck_analysis_runs_progress_requires_start, ck_analysis_runs_queued_not_started, ck_analysis_runs_status_valid, ck_analysis_runs_time_order | ix_analysisrun_project_created, ix_analysisrun_status_created |
| endpoints | uq_endpoints_run_path_method | ck_endpoints_http_method_valid, ck_endpoints_path_not_blank, ck_endpoints_unsupported_has_reason, ck_endpoints_unsupported_reason_valid | — |
| generated_tests | uq_generated_tests_run_module_name | ck_generated_tests_code_sha256_format, ck_generated_tests_expected_status_range, ck_generated_tests_method_valid, ck_generated_tests_module_format, ck_generated_tests_name_format, ck_generated_tests_repair_count_range, ck_generated_tests_validation_status_valid | ix_gentest_endpoint |
| test_executions | uq_test_executions_test_attempt | ck_test_executions_attempt_positive, ck_test_executions_duration_non_negative, ck_test_executions_duration_requires_finish, ck_test_executions_error_origin_valid, ck_test_executions_error_type_valid, ck_test_executions_not_run_not_started, ck_test_executions_observed_status_range, ck_test_executions_outcome_requires_start, ck_test_executions_queued_not_started, ck_test_executions_running_started, ck_test_executions_status_valid, ck_test_executions_technical_error_has_type, ck_test_executions_terminal_finished, ck_test_executions_time_order | — |
| security_findings | uq_security_findings_run_fingerprint | ck_security_findings_classification_valid, ck_security_findings_file_path_relative, ck_security_findings_fingerprint_format, ck_security_findings_line_number_positive, ck_security_findings_rule_id_not_blank, ck_security_findings_severity_valid, ck_security_findings_source_valid, ck_security_findings_title_not_blank | ix_finding_endpoint, ix_finding_execution, ix_finding_run_severity |
| reports | — | ck_reports_file_path_relative, ck_reports_file_size_non_negative, ck_reports_format_valid, ck_reports_scope_valid | ix_report_run_created |
| llm_calls | — | ck_llm_calls_latency_non_negative, ck_llm_calls_model_not_blank, ck_llm_calls_provider_valid, ck_llm_calls_purpose_valid, ck_llm_calls_status_valid, ck_llm_calls_success_has_tokens, ck_llm_calls_tokens_non_negative | ix_llmcall_generated_test, ix_llmcall_run_created |

Toplam 85 adlandırılmış kısıt/indeks; her biri SQL'de ve ORM `Meta` içinde aynı adla bulunur. Açık indeks adları Django'nun 30 karakter sınırına uygundur.

### C.3 Bilinçli farklar

PK/FK kısıt adları, sütun `DEFAULT` ifadelerinin konumu (veritabanı / Python), `updated_at` güncelleme mekanizması, `CASCADE`/`SET_NULL` davranışının uygulandığı katman ve `CHECK` ifadelerinin metinsel yazımı iki dosya arasında farklıdır; anlam aynıdır. Ayrıntı ve çözüm: veri sözlüğü 14.2 (F1–F9).

## D. AnalysisRun Yaşam Döngüsü

### D.1 Geçiş matrisi

| Kaynak | Hedef | Tetikleyici | Zaman damgası değişikliği |
|---|---|---|---|
| (yeni) | QUEUED | API çalıştırma oluşturur, yöntem ve modeli, gereksinim anlık görüntüsünü yazar, görevi kuyruğa gönderir ve `celery_task_id`'yi kaydeder (ekran 05) | created_at |
| QUEUED | ANALYZING | İşçi görevi alır | started_at = şimdi |
| ANALYZING | GENERATING | AST analizi tamamlanır; `ast_results` ve `endpoints` satırları yazılır (ekran 06) | — |
| GENERATING | VALIDATING | Testler üretilir; dil modeli çağrıları `llm_calls`'a yazılır (ekran 07) | — |
| VALIDATING | EXECUTING | Testlerin sözdizimi ve politika doğrulaması biter | — |
| EXECUTING | SCANNING | VALID testler sandbox'ta yürütülür; gerekirse tek düzeltme yapılır (ekran 08) | — |
| SCANNING | COMPLETED | Bandit, check --deploy ve yetkilendirme testi bulguları yazılır (ekran 09) | finished_at = şimdi |
| QUEUED | FAILED | İşçi başlamadan hata (ör. `QUEUE_ERROR`) | finished_at = şimdi; started_at NULL kalır |
| ANALYZING … SCANNING | FAILED | Aşama hatası, sandbox başlatılamaması (`RUNNER_START_ERROR`, ekran 17), işçi kaybı | finished_at = şimdi |
| QUEUED … SCANNING | CANCELLED | Kullanıcı onayıyla durdurma (ekran 28, 29); görev iptal, sandbox silinir, açık denemeler STOPPED / NOT_RUN | finished_at = şimdi |

COMPLETED, FAILED ve CANCELLED son durumlardır; geri geçiş yoktur. FAILED durumunda `error_code` zorunludur (değerler sözlük 8.6). CANCELLED'da tamamlanan test sonuçları ve bulgular saklanır. Otomatik yeniden deneme yapılmaz; yeniden başlatma yeni bir AnalysisRun oluşturur.

### D.2 Zorlama düzeyi

| Kural | Zorlayan |
|---|---|
| Durum dokuz değerden biridir | Veritabanı (`ck_analysis_runs_status_valid`) ve TextChoices |
| Durum ile `started_at` / `finished_at` tutarlıdır | Veritabanı (`ck_analysis_runs_queued_not_started`, `ck_analysis_runs_progress_requires_start`, `ck_analysis_runs_finished_iff_terminal`, `ck_analysis_runs_time_order`) |
| FAILED'da hata kodu vardır | Veritabanı (`ck_analysis_runs_failure_has_error_code`) |
| Yöntem ile sağlayıcı/model tutarlıdır | Veritabanı (`ck_analysis_runs_llm_settings`) |
| Projede tek aktif çalıştırma (QUEUED … SCANNING) | Veritabanı (`uq_analysis_runs_one_active_per_project`) |
| Geçiş sırası (D.1), iptal adımları, rapor kapsamı | Yalnızca uygulama katmanı: koşullu `UPDATE ... WHERE status = <beklenen>` veya `select_for_update()` |

Veritabanı `CHECK` kısıtları geçiş sırasını tek başına zorlamaz; satırın önceki değerini göremezler. Bu nedenle tüm durum değişiklikleri tek bir servis fonksiyonundan geçmelidir.

## E. ER Diyagramı Tanımı

### E.1 Varlıklar ve anahtar alanlar

| Varlık | PK | FK | Diyagramda gösterilecek diğer alanlar |
|---|---|---|---|
| User (`auth_user`, çerçeve yönetimli) | id (integer) | — | username (Django alanı; yalnızca etiket amaçlı) |
| Project (`projects`) | id (bigint) | owner_id → User.id | name, description, source_type, source_archive, source_directory, archive_sha256, validation_status, validation_report, created_at, updated_at |
| ReferenceRequirement (`reference_requirements`) | id (bigint) | project_id → Project.id | requirement_code, category, source, title, description, expected_result, specification, is_active, revision, created_at, updated_at |
| AnalysisRun (`analysis_runs`) | id (bigint) | project_id → Project.id | status, method, llm_provider, llm_model, fallback_enabled, celery_task_id, requirements_snapshot, ast_results, processing_metadata, coverage_percent, error_code, error_message, created_at, started_at, finished_at, updated_at |
| Endpoint (`endpoints`) | id (bigint) | analysis_run_id → AnalysisRun.id | path, http_method, view_name, auth_type, permission_classes, is_supported, unsupported_reason, created_at |
| GeneratedTest (`generated_tests`) | id (bigint) | analysis_run_id → AnalysisRun.id, endpoint_id → Endpoint.id (NULL) | test_module, test_name, generation_method, requirement_code, role, expected_status, is_security_test, source_code, code_sha256, validation_status, validation_errors, repair_count, generation_metadata, created_at, updated_at |
| TestExecution (`test_executions`) | id (bigint) | generated_test_id → GeneratedTest.id | attempt_number, status, observed_status, error_type, error_origin, started_at, finished_at, duration_ms, output_excerpt, error_summary, result_details, created_at |
| SecurityFinding (`security_findings`) | id (bigint) | analysis_run_id → AnalysisRun.id, test_execution_id → TestExecution.id (NULL), endpoint_id → Endpoint.id (NULL) | source, rule_id, severity, classification, title, description, file_path, line_number, evidence_excerpt, recommendation_key, details, fingerprint, created_at |
| Report (`reports`) | id (bigint) | analysis_run_id → AnalysisRun.id | format, scope, sections, file_path, file_size_bytes, created_at |
| LlmCall (`llm_calls`) | id (bigint) | analysis_run_id → AnalysisRun.id, generated_test_id → GeneratedTest.id (NULL) | provider, model, purpose, prompt_tokens, completion_tokens, latency_ms, status, error_message, created_at |
| Giriş kilidi (django-axes, çerçeve yönetimli) | — | — | Tablo adları: axes_accessattempt, axes_accesslog, axes_accessfailurelog, axes_accessattemptexpiration; sütunları gösterilmez, bağlantı çizgisi yoktur |

### E.2 İlişkiler (crow's foot gösterimi)

| No | İlişki | Üst uç | Alt uç | Etiket |
|---|---|---|---|---|
| R1 | User — Project | tam bir (`\|\|`) | sıfır veya çok (`o{`) | sahibidir |
| R2 | Project — ReferenceRequirement | tam bir (`\|\|`) | sıfır veya çok (`o{`) | tanımlar |
| R3 | Project — AnalysisRun | tam bir (`\|\|`) | sıfır veya çok (`o{`) | analiz edilir |
| R4 | AnalysisRun — Endpoint | tam bir (`\|\|`) | sıfır veya çok (`o{`) | bulur |
| R5 | AnalysisRun — GeneratedTest | tam bir (`\|\|`) | sıfır veya çok (`o{`) | üretir |
| R6 | Endpoint — GeneratedTest | sıfır veya bir (`\|o`) | sıfır veya çok (`o{`) | hedefler |
| R7 | GeneratedTest — TestExecution | tam bir (`\|\|`) | sıfır veya çok (`o{`) | yürütülür |
| R8 | AnalysisRun — SecurityFinding | tam bir (`\|\|`) | sıfır veya çok (`o{`) | raporlar |
| R9 | TestExecution — SecurityFinding | sıfır veya bir (`\|o`) | sıfır veya çok (`o{`) | kanıtlar |
| R10 | Endpoint — SecurityFinding | sıfır veya bir (`\|o`) | sıfır veya çok (`o{`) | ilgilidir |
| R11 | AnalysisRun — Report | tam bir (`\|\|`) | sıfır veya çok (`o{`) | dışa aktarır |
| R12 | AnalysisRun — LlmCall | tam bir (`\|\|`) | sıfır veya çok (`o{`) | çağırır |
| R13 | GeneratedTest — LlmCall | sıfır veya bir (`\|o`) | sıfır veya çok (`o{`) | üretir/düzeltir |

Diyagramda bulunmaması gereken ilişkiler: TestExecution — AnalysisRun, GeneratedTest — ReferenceRequirement, ReferenceRequirement — Endpoint, django-axes tabloları ile herhangi bir varlık arasında çizgi, User ile Project dışındaki herhangi bir varlık arasında doğrudan çizgi, çoka çok ilişki.

### E.3 Mermaid tanımı

GitHub üzerinde doğrudan görüntülenebilir. Kaynak dosya `er_diagram_source.mmd`'dir; aşağıdaki blok onunla aynıdır. Bileşik ve kısmi tekil kısıtlar Mermaid'de ifade edilemediği için öznitelik yorumu olarak yazılmıştır; yalnızca gerçekten tek sütunlu tekil olan `celery_task_id` `UK` ile işaretlidir.

```mermaid
---
title: "ER Diyagramı — Tam Teknik Şema (TestKalkan, revizyon 2)"
---
%% Kaynak: database_schema.sql (PostgreSQL 16 kataloğundan üretilmiştir)
%% U1 = bileşik tekil kısıt üyesi; UQ = tek sütunlu tekil; UP = kısmi tekil indeks.
%% Mermaid bileşik ve kısmi tekil kısıtları ifade edemez; bunlar yorum olarak verilir.
%% |o--o{ : FK NULL olabilir (isteğe bağlı çapraz başvuru, on_delete=SET_NULL).
%% Çerçeve yönetimli django-axes tabloları (FK'siz, şemada tanımlanmaz): axes_accessattempt, axes_accesslog, axes_accessfailurelog, axes_accessattemptexpiration
erDiagram
    auth_user ||--o{ projects : "R1 sahibidir"
    projects ||--o{ reference_requirements : "R2 tanımlar"
    projects ||--o{ analysis_runs : "R3 analiz edilir"
    analysis_runs ||--o{ endpoints : "R4 bulur"
    analysis_runs ||--o{ generated_tests : "R5 üretir"
    endpoints |o--o{ generated_tests : "R6 hedefler"
    generated_tests ||--o{ test_executions : "R7 yürütülür"
    analysis_runs ||--o{ security_findings : "R8 raporlar"
    test_executions |o--o{ security_findings : "R9 kanıtlar"
    endpoints |o--o{ security_findings : "R10 ilgilidir"
    analysis_runs ||--o{ reports : "R11 dışa aktarır"
    analysis_runs ||--o{ llm_calls : "R12 çağırır"
    generated_tests |o--o{ llm_calls : "R13 üretir/düzeltir"

    auth_user["User (auth_user)"] {
        integer id PK "Django tarafından yönetilir"
        varchar username "Django alanı; yalnızca etiket amaçlı"
    }
    projects["Project (projects)"] {
        bigint id PK
        integer owner_id FK "U1: UNIQUE (owner_id, name)"
        varchar(150) name "U1: UNIQUE (owner_id, name)"
        text description
        varchar(20) source_type
        varchar(255) source_archive "NULL olabilir"
        varchar(500) source_directory "NULL olabilir"
        varchar(64) archive_sha256 "NULL olabilir"
        varchar(20) validation_status
        jsonb validation_report
        timestamptz created_at
        timestamptz updated_at
    }
    reference_requirements["ReferenceRequirement (reference_requirements)"] {
        bigint id PK
        bigint project_id FK "U1: UNIQUE (project_id, requirement_code)"
        varchar(50) requirement_code "U1: UNIQUE (project_id, requirement_code)"
        varchar(30) category
        varchar(20) source
        varchar(200) title
        text description
        text expected_result
        jsonb specification
        boolean is_active
        integer revision
        timestamptz created_at
        timestamptz updated_at
    }
    analysis_runs["AnalysisRun (analysis_runs)"] {
        bigint id PK
        bigint project_id FK "UP: UNIQUE (project_id) WHERE status ∈ {QUEUED, ANALYZING, GENERATING, VALIDATING, EXECUTING, SCANNING}"
        varchar(20) status "CHECK: QUEUED, ANALYZING, GENERATING, VALIDATING, EXECUTING, SCANNING, COMPLETED, FAILED, CANCELLED"
        varchar(20) method
        varchar(20) llm_provider "NULL olabilir"
        varchar(100) llm_model "NULL olabilir"
        boolean fallback_enabled
        varchar(255) celery_task_id UK "tek sütun tekil; NULL değerler hariç; NULL olabilir"
        jsonb requirements_snapshot
        jsonb ast_results
        jsonb processing_metadata
        numeric(5,2) coverage_percent "NULL olabilir"
        varchar(50) error_code
        varchar(2000) error_message
        timestamptz created_at
        timestamptz started_at "NULL olabilir"
        timestamptz finished_at "NULL olabilir"
        timestamptz updated_at
    }
    endpoints["Endpoint (endpoints)"] {
        bigint id PK
        bigint analysis_run_id FK "U1: UNIQUE (analysis_run_id, path, http_method)"
        varchar(500) path "U1: UNIQUE (analysis_run_id, path, http_method)"
        varchar(10) http_method "U1: UNIQUE (analysis_run_id, path, http_method)"
        varchar(255) view_name
        varchar(50) auth_type
        jsonb permission_classes
        boolean is_supported
        varchar(50) unsupported_reason "NULL olabilir"
        timestamptz created_at
    }
    generated_tests["GeneratedTest (generated_tests)"] {
        bigint id PK
        bigint analysis_run_id FK "U1: UNIQUE (analysis_run_id, test_module, test_name)"
        bigint endpoint_id FK "NULL olabilir"
        varchar(150) test_module "U1: UNIQUE (analysis_run_id, test_module, test_name)"
        varchar(150) test_name "U1: UNIQUE (analysis_run_id, test_module, test_name)"
        varchar(20) generation_method
        varchar(50) requirement_code
        varchar(50) role
        smallint expected_status "NULL olabilir"
        boolean is_security_test
        text source_code
        varchar(64) code_sha256
        varchar(20) validation_status
        jsonb validation_errors
        smallint repair_count
        jsonb generation_metadata
        timestamptz created_at
        timestamptz updated_at
    }
    test_executions["TestExecution (test_executions)"] {
        bigint id PK
        bigint generated_test_id FK "U1: UNIQUE (generated_test_id, attempt_number)"
        integer attempt_number "U1: UNIQUE (generated_test_id, attempt_number)"
        varchar(20) status
        smallint observed_status "NULL olabilir"
        varchar(20) error_type "NULL olabilir"
        varchar(20) error_origin "NULL olabilir"
        timestamptz started_at "NULL olabilir"
        timestamptz finished_at "NULL olabilir"
        integer duration_ms "NULL olabilir"
        varchar(10000) output_excerpt
        varchar(2000) error_summary
        jsonb result_details
        timestamptz created_at
    }
    security_findings["SecurityFinding (security_findings)"] {
        bigint id PK
        bigint analysis_run_id FK "U1: UNIQUE (analysis_run_id, fingerprint)"
        bigint test_execution_id FK "NULL olabilir"
        bigint endpoint_id FK "NULL olabilir"
        varchar(20) source
        varchar(100) rule_id
        varchar(10) severity
        varchar(20) classification
        varchar(255) title
        text description
        varchar(500) file_path
        integer line_number "NULL olabilir"
        varchar(1000) evidence_excerpt
        varchar(50) recommendation_key "NULL olabilir"
        jsonb details
        varchar(64) fingerprint "U1: UNIQUE (analysis_run_id, fingerprint)"
        timestamptz created_at
    }
    reports["Report (reports)"] {
        bigint id PK
        bigint analysis_run_id FK
        varchar(10) format
        varchar(10) scope
        jsonb sections
        varchar(500) file_path
        bigint file_size_bytes
        timestamptz created_at
    }
    llm_calls["LlmCall (llm_calls)"] {
        bigint id PK
        bigint analysis_run_id FK
        bigint generated_test_id FK "NULL olabilir"
        varchar(20) provider
        varchar(100) model
        varchar(20) purpose
        integer prompt_tokens "NULL olabilir"
        integer completion_tokens "NULL olabilir"
        integer latency_ms "NULL olabilir"
        varchar(20) status
        varchar(2000) error_message "NULL olabilir"
        timestamptz created_at
    }
```

## F. Dosyalar Arası Tutarlılık Kontrol Listesi

| Kontrol | Sonuç | Yöntem |
|---|---|---|
| Her SQL uygulama tablosu bir ORM modeline (`db_table`) karşılık gelir | Sağlandı (9/9) | Otomatik karşılaştırma |
| Her ORM alanı bir SQL sütununa karşılık gelir; tip, NULL durumu ve uzunluk aynıdır | Sağlandı (122/122) | Otomatik karşılaştırma |
| Her veri sözlüğü satırı gerçek şemadaki bir sütuna karşılık gelir; eksik sütun yoktur | Sağlandı (122/122) | Otomatik karşılaştırma |
| Her FK var olan bir tablo ve anahtara işaret eder; NULL durumu ve ORM `on_delete` (CASCADE / SET_NULL) beklenenle aynıdır | Sağlandı (13/13) | DDL'in PostgreSQL'de çalıştırılması ve otomatik karşılaştırma |
| Durum değerleri tüm dosyalarda aynıdır (AnalysisRun 9, TestExecution 7, GeneratedTest doğrulama 4) | Sağlandı | Otomatik ayrıştırma ve senaryo testleri |
| Her JSONB sütununun ORM karşılığı `JSONField`'dır (11 alan) | Sağlandı | Otomatik karşılaştırma |
| Adlandırılmış tekil/CHECK kısıtları ve açık indeksler iki dosyada aynı adla vardır (85) | Sağlandı | Otomatik karşılaştırma |
| `default=dict` / `default=list` kullanılır, değiştirilebilir sabit nesne varsayılanı yoktur | Sağlandı | Elle inceleme |
| `related_name` değerleri çakışmaz | Sağlandı | Elle inceleme |
| Belgelenen her ilişki ER diyagramında gösterilir ve E.2 ile örtüşür | Sağlandı | SVG'lerin otomatik doğrulaması (H) |
| Kaldırılan sütun ve değerler hiçbir dosyada kalmadı (`retry_count`, `source_repository_url`, REPOSITORY, HYBRID test kökeni, eski kategori/kaynak/önem/sınıf değerleri) | Sağlandı | Senaryo testleri (P06, P11, A29, G03, R05, S04–S06) ve metin araması |
| Gizli değer saklayan alan yoktur | Sağlandı | Elle inceleme |

### F.1 Uç senaryoların karşılanması

Senaryo kimlikleri (P01, A13 …) H bölümündeki davranış testlerine karşılık gelir.

| No | Senaryo | Şemadaki karşılığı | Test |
|---|---|---|---|
| 1 | Bir kullanıcı birden çok proje oluşturur; aynı ad tekrar edilemez | User 1:N Project; ad, sahip başına tekil | P09, P10 |
| 2 | Proje arşivden veya izinli dizinden alınır; tek kaynak (ekran 03) | ARCHIVE: anahtar ve özet zorunlu, dizin NULL; ALLOWED_DIRECTORY: göreli dizin zorunlu, arşiv sütunları NULL | P01–P08, P12–P20 |
| 3 | Roller, erişim kuralları ve dağıtım beklentileri ayrı satırlar (ekran 04, 23) | `category` ROLE / ACCESS_RULE / DEPLOY_EXPECTATION; ROLE'de beklenen sonuç boş | R01–R05 |
| 4 | Kurallar JSON dosyasıyla yüklenir (ekran 31) | `source = JSON_UPLOAD`; varsayılan FORM | R03, R06, R07 |
| 5 | Analiz yöntemi, modeli ve fallback seçilir (ekran 05, 24) | `method`, `llm_provider`, `llm_model` tutarlılık kısıtı; `fallback_enabled` varsayılanı true | A01–A07, A30 |
| 6 | Analiz aşamaları VALIDATING ve SCANNING'den geçer (ekran 16) | Dokuz durum, zaman damgası kısıtları | A08–A12, A16 |
| 7 | Projede ikinci aktif analiz açılamaz | Kısmi tekil indeks, aktif küme 6 durum | A17–A20 |
| 8 | Analiz kullanıcı tarafından durdurulur (ekran 28, 29) | CANCELLED, `finished_at` zorunlu; denemeler STOPPED / NOT_RUN | A13–A15, A19, T07–T10 |
| 9 | Sandbox başlatılamaz (ekran 17) | FAILED + `RUNNER_START_ERROR`; otomatik yeniden deneme yok, `retry_count` yok | A24–A26, A29 |
| 10 | Kod kapsamı gösterilir (ekran 08) | `coverage_percent` 0–100 | A21–A23 |
| 11 | AST endpointleri listelenir, kapsam dışılar işaretlenir (ekran 06) | `endpoints`; HEAD/OPTIONS reddedilir; kapsam dışı neden zorunlu | E01–E12 |
| 12 | Test endpoint, rol ve beklenen kodla üretilir (ekran 07) | `endpoint_id`, `role`, `expected_status`, `is_security_test` | G01, G02, G07, G08 |
| 13 | Test en fazla bir kez düzeltilir | `repair_count` 0–1; düzeltme sonrası yeni deneme numarası | G04–G06, T16 |
| 14 | PASS / FAIL / teknik hata ayrımı (ekran 08) | Yedi durum; TECHNICAL_ERROR'da `error_type` zorunlu; gözlenen kod | T01–T06, T11–T15, T17–T23 |
| 15 | Bulgu test ile kanıtlanır, düzeltme önerisi gösterilir (ekran 09) | `test_execution_id`, `endpoint_id`, `recommendation_key`; yeni kaynak/önem/sınıf değerleri | S01–S09 |
| 16 | Rapor PDF/JSON, tam/kısmi olarak alınır (ekran 10, 21, 25) | `reports`; biçim, kapsam, göreli dosya yolu, boyut | D01–D07 |
| 17 | Token kullanımı ve kota aşımı izlenir (ekran 02, 24; İST-13) | `llm_calls`; başarılı çağrıda token zorunlu, kota aşımında NULL | L01–L11 |
| 18 | Proje silinir (ekran 30) | ORM CASCADE / SET_NULL; ham SQL silme reddedilir; dosyalar uygulama tarafından silinir | X01–X04 |
| 19 | Kullanıcı başkasının analizine erişemez (ekran 13) | Sahiplik zinciriyle süzme; 403 (sözlük 13.1). Uygulama katmanı | — |
| 20 | Yinelenen görev teslimi | Tekil `celery_task_id`; endpoint, test, deneme ve bulgu doğal anahtarları | A28, E08, T15, S08 |

## G. Issue #24 Kabul Ölçütleri

| No | Kabul ölçütü | Karşılayan dosya ve bölüm |
|---|---|---|
| 1 | Gerekli tüm varlıklar ve ilişkiler tanımlanmıştır | `database_schema.sql` bölüm 1–9; `django_models.py` dokuz model ve `AUTH_USER_MODEL`; `data_dictionary.md` bölüm 3 ve 6; bu belge A ve B |
| 2 | PostgreSQL veri tipleri, PK/FK kısıtları ve önemli bütünlük kuralları belgelenmiştir | `data_dictionary.md` bölüm 4, 5, 7, 14; `database_schema.sql` kısıt tanımları; bu belge C |
| 3 | AnalysisRun durumları, Celery görev kimliği ve zaman damgaları eksiksiz tanımlanmıştır | `data_dictionary.md` 4.4 ve bölüm 8; `database_schema.sql` bölüm 3; `django_models.py` `AnalysisRun.Status`; bu belge D |
| 4 | Veri sözlüğü tüm tabloları ve sütunları kapsar | `data_dictionary.md` 4.1–4.11 (122 sütun, `auth_user.id` ve django-axes tabloları); bu belge F |
| 5 | İlişkisel tasarım ER diyagramında tutarlı biçimde gösterilebilir | Bu belge E; `data_dictionary.md` bölüm 15; `er_diagram_full.svg`, `er_diagram_presentation.svg` |
| 6 | Dosyalar GitHub deposuna eklenmeye hazırdır | `docs/database/` altındaki dört dosya; doğrulama durumu bu belge H |
| 7 | Şema mockup'taki her bilgiyi saklayabilir ve mockup'ta olmayan bir özelliği ima etmez | Bu belge I; `data_dictionary.md` bölüm 1 (kapsam dışı olanlar) |

İlgili gereksinimler İST-01, İST-03, İST-04, İST-07, İST-08, İST-09, İST-13 ve İST-15'tir. Bu gereksinimlerin metinleri bu pakette yer almadığından şema öğeleriyle tek tek eşleştirilmemiştir; eşleştirme gereksinim belgesi üzerinden yapılmalıdır.

## H. Doğrulama Durumu (Revizyon 2)

| Kontrol | Durum | Ayrıntı |
|---|---|---|
| Tasarım incelemesi | Yapıldı | Mockup README'si (ekran listesi, Kapsam notları, Diyagramlarla tutarlılık) ve revizyon isteğinin on maddesi üzerinden. |
| Referans SQL'in çalıştırılması | Yapıldı | PostgreSQL 16.15 üzerinde geçici bir veritabanında. `auth_user` yerine yalnızca `id integer` ve `username` sütunlarını içeren geçici bir tablo kullanıldı. DDL hatasız uygulandı; 9 tablo ve 26 indeks oluştu. |
| Kısıt davranış senaryoları | Yapıldı | Aynı DDL ile ayrı bir veritabanında 132 senaryo (53 kabul, 79 red beklenen) her biri kendi işleminde çalıştırıldı; 132'i beklendiği gibi sonuçlandı. Red senaryolarında hatanın beklenen kısıt adıyla geldiği doğrulandı. Silme senaryoları ORM `CASCADE`/`SET_NULL` sırası SQL ile taklit edilerek çalıştırıldı. |
| `django_models.py` Python sözdizimi | Yapıldı | `python -m py_compile` başarılı. |
| ORM–SQL–sözlük otomatik karşılaştırması | Yapıldı | Modeller Python `ast` ile, sözlük bölüm 4 tabloları metin olarak ayrıştırıldı ve PostgreSQL kataloğuyla karşılaştırıldı: 122 sütunda ad, sıra, tip, NULL durumu ve uzunluk; 13 FK'de hedef, NULL durumu ve `on_delete`; 85 adlandırılmış kısıt/indeks. Fark bulunmadı. Bu karşılaştırma Django'yu çalıştırmaz; ORM alanlarının PostgreSQL tiplerine dönüşümü Django'nun belgelenmiş eşlemesine göre yapılmıştır. |
| ER diyagramlarının otomatik doğrulaması | Yapıldı | SVG'ler XML olarak geri okundu: tam diyagram 224, sunum 195 kontrolün tamamı geçti (alanlar, tipler, anahtarlar, 13 ilişkinin uç sembolleri, çizgi–kart ve çizgi–çizgi kesişimi, etiket çakışması, metin taşması). Doğrulayıcı, bilerek bozulmuş SVG kopyalarında hataları yakaladı. |
| Mermaid kaynağı | Yapıldı | mermaid-cli 11.16.0 ile hatasız render edildi; öznitelikler, anahtarlar, NULL yorumları ve 13 ilişkinin isteğe bağlılığı matrisle aynı. |
| Django sistem kontrolleri (`manage.py check`) | Yapılmadı | Doğrulama ortamında Django paketi kurulamadı (paket deposunda erişilebilir sürüm yoktu). |
| `makemigrations` / `sqlmigrate` çıktısının referans SQL ile karşılaştırılması | Yapılmadı | Aynı nedenle. |
| django-axes tablo seti | Kısmen | django-axes 9.0.0 kaynak kodundaki modeller ve migration'lar incelendi; projede kullanılacak sürüm sabitlendiğinde liste yeniden doğrulanmalıdır. |

Django ortamında yapılması gereken doğrulama adımları:

1. Modelleri uygulamanın `models.py` dosyasına taşıyın ve `python manage.py check` çalıştırın.
2. `python manage.py makemigrations` ile ilk migration'ı oluşturun.
3. `python manage.py sqlmigrate <app_label> 0001` çıktısında tablo, sütun, tekil/CHECK kısıt ve indeks adlarını bu belgenin C bölümüyle karşılaştırın. PK/FK adlarının farklı olması beklenir (sözlük 14.2 F1).
4. Boş bir test veritabanında `python manage.py migrate` çalıştırın ve modeller için temel oluşturma/silme testleri yazın; özellikle proje silindiğinde alt kayıtların silindiğini ve isteğe bağlı başvuruların `NULL` yapıldığını doğrulayın.

## I. Revizyon 2 Değişiklikleri ve Mockup Karşılıkları

Tam değişiklik listesi ve her değişikliğin karşılık geldiği mockup ekranı veya kararı `er_diagram_review.md` bölüm 3'tedir.

