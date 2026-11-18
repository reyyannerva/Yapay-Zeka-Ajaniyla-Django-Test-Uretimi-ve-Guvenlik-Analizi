# H4-01 (#33) — Migration, PostgreSQL ve Test Kanıtı

Bu dosyadaki çıktılar 2026-11-18 tarihinde, boş bir PostgreSQL veritabanı (`h401_dev`, yerel geliştirme kümesi) yeniden oluşturulduktan sonra aşağıdaki komutların gerçek çıktılarıdır. Ortam: Python 3.13.18, Django 5.2.19, DRF 3.18.3, django-axes 9.0.0, psycopg 3.3.9, PostgreSQL 16.15. Parolalar ve gizli anahtar çıktılarda yer almaz.

## 1. Bağlantı, migration ve sistem kontrolü

```text
$ python manage.py check_database
Bağlantı başarılı: h401_app@h401_dev — PostgreSQL 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) on x86_64-pc-linux-gnu, compiled by gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0, 64-bit
[exit: 0]

$ python manage.py makemigrations
No changes detected
[exit: 0]

$ python manage.py makemigrations --check --dry-run
No changes detected
[exit: 0]

$ python manage.py migrate
Operations to perform:
  Apply all migrations: admin, auth, axes, contenttypes, core, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying axes.0001_initial... OK
  Applying axes.0002_auto_20151217_2044... OK
  Applying axes.0003_auto_20160322_0929... OK
  Applying axes.0004_auto_20181024_1538... OK
  Applying axes.0005_remove_accessattempt_trusted... OK
  Applying axes.0006_remove_accesslog_trusted... OK
  Applying axes.0007_alter_accessattempt_unique_together... OK
  Applying axes.0008_accessfailurelog... OK
  Applying axes.0009_add_session_hash... OK
  Applying axes.0010_accessattemptexpiration... OK
  Applying core.0001_initial... OK
  Applying sessions.0001_initial... OK
[exit: 0]

$ python manage.py migrate
Operations to perform:
  Apply all migrations: admin, auth, axes, contenttypes, core, sessions
Running migrations:
  No migrations to apply.
[exit: 0]

$ python manage.py check
System check identified no issues (1 silenced).
[exit: 0]

$ python manage.py showmigrations core axes
core
 [X] 0001_initial
axes
 [X] 0001_initial
 [X] 0002_auto_20151217_2044
 [X] 0003_auto_20160322_0929
 [X] 0004_auto_20181024_1538
 [X] 0005_remove_accessattempt_trusted
 [X] 0006_remove_accesslog_trusted
 [X] 0007_alter_accessattempt_unique_together
 [X] 0008_accessfailurelog
 [X] 0009_add_session_hash
 [X] 0010_accessattemptexpiration
[exit: 0]

```

## 2. Veritabanı kataloğu (migration sonrası)

```text
tablo: analysis_runs, endpoints, generated_tests, llm_calls, projects, reference_requirements, reports, security_findings, test_executions
uygulama sütunu: 122
CHECK: 70, UNIQUE: 7, FK: 13
jsonb sütunu: 11
axes tabloları: axes_accessattempt, axes_accessattemptexpiration, axes_accessfailurelog, axes_accesslog
kısmi tekil indeks: CREATE UNIQUE INDEX uq_analysis_runs_one_active_per_project ON public.analysis_runs USING btree (project_id) WHERE ((status)::text = ANY ((ARRAY['QUEUED'::character varying, 'ANALYZING'::character varying, 'GENERATING'::character varying, 'VALIDATING'::character varying, 'EXECUTING'::character varying, 'SCANNING'::character varying])::text[]))
ck_analysis_runs_status_valid: CHECK (((status)::text = ANY ((ARRAY['QUEUED'::character varying, 'ANALYZING'::character varying, 'GENERATING'::character varying, 'VALIDATING'::character varying, 'EXECUTING'::character varying, 'SCANNING'::character varying, 'COMPLETED'::character varying, 'FAILED'::character varying, 'CANCELLED'::character varying])::text[])))
ck_reference_requirements_access_rule_method: CHECK (((NOT ((category)::text = 'ACCESS_RULE'::text)) OR ((specification ? 'method'::text) AND ((specification -> 'method'::text) = ANY (ARRAY['"GET"'::jsonb, '"POST"'::jsonb, '"PUT"'::jsonb, '"PATCH"'::jsonb, '"DELETE"'::jsonb])))))
ck_test_executions_status_valid: CHECK (((status)::text = ANY ((ARRAY['PENDING'::character varying, 'RUNNING'::character varying, 'PASS'::character varying, 'FAIL'::character varying, 'ERROR'::character varying, 'TIMEOUT'::character varying, 'STOPPED'::character varying, 'NOT_RUN'::character varying])::text[])))
ck_test_executions_timeout_consistent: CHECK (((((error_type)::text = 'TIMEOUT'::text) AND (error_type IS NOT NULL) AND ((status)::text = 'TIMEOUT'::text)) OR ((NOT ((status)::text = 'TIMEOUT'::text)) AND ((error_type IS NULL) OR (NOT (((error_type)::text = 'TIMEOUT'::text) AND (error_type IS NOT NULL)))))))
uq_analysis_runs_celery_task_id: UNIQUE (celery_task_id)
```

## 3. Referans DDL ile karşılaştırma

`docs/database/database_schema.sql` ayrı, boş bir veritabanına (`migrate auth` sonrası) `psql -v ON_ERROR_STOP=1` ile hatasız uygulanmış ve migration ile oluşan şemayla karşılaştırılmıştır:

* 122 sütun (tablo, ad, tip, uzunluk, NULL olabilirlik): **fark yok**
* 87 adlandırılmış CHECK / UNIQUE / ix_* / uq_* indeks adı: **fark yok**
* Yeni kısıtların NULL sınır durumları referans DDL'de de aynı davranır (`{}` ve `HEAD` reddedildi; `TIMEOUT` + `error_type NULL` reddedildi; `TIMEOUT` + `error_type TIMEOUT` kabul edildi).

## 4. Testler

```text
$ python -m pytest -q -p no:randomly
........................................................................ [ 40%]
........................................................................ [ 80%]
..................................                                       [100%]
178 passed in 40.21s
[exit: 0]

```

Dosya başına test sayısı:

```text
     32 core/tests/test_analysis_run.py
      7 core/tests/test_auth_lockout.py
     14 core/tests/test_generated_test.py
      3 core/tests/test_progress.py
     11 core/tests/test_project.py
     36 core/tests/test_requirement.py
      8 core/tests/test_schema.py
     13 core/tests/test_security_finding.py
     11 core/tests/test_settings_env.py
      8 core/tests/test_support_models.py
     35 core/tests/test_test_execution.py
```
