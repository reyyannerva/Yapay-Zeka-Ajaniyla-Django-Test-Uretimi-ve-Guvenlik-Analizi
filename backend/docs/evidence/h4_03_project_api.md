# H4-03 (#35) — Gerçek İstek-Yanıt, PostgreSQL ve Test Kanıtı

Ortam: Python 3.13.18, Django 5.2.19, DRF 3.18.3, djangorestframework-simplejwt 5.5.1, PostgreSQL 16.15 (yerel geliştirme kümesi). Tarih: 2026-11-18.

İstekler `python manage.py runserver` ile çalışan gerçek sunucuya `curl` ile gönderilmiştir. Sunucu
`PROJECT_UPLOAD_MAX_BYTES=200000` ile başlatılmıştır (413 örneği için). Kullanıcılar (`demo_alice`,
`demo_bob`) geçici demo hesaplarıdır. Token'lar `POST /api/auth/login/` ile alınmış ve bu dosyaya
**yazılmamıştır**. Yanıt gövdeleri olduğu gibidir (yalnızca JSON girintilenmiştir).

## 1. Migration ve sistem kontrolü

```text
$ python manage.py check
System check identified no issues (1 silenced).

$ python manage.py makemigrations --check --dry-run
No changes detected

$ python manage.py migrate
Operations to perform:
  Apply all migrations: admin, auth, axes, contenttypes, core, sessions, token_blacklist
Running migrations:
  No migrations to apply.

$ python manage.py showmigrations core
core
 [X] 0001_initial
 [X] 0002_project_archive_private_storage

$ python manage.py sqlmigrate core 0002
BEGIN;
--
-- Alter field source_archive on project
--
-- (no-op)
COMMIT;
```

## 2. İstek-yanıt örnekleri

```text
### 1) Kimlik doğrulamasız liste
{
  "detail": "Giriş bilgileri verilmedi."
}
HTTP 401

### 2) Geçersiz token
{
  "detail": "Verilen token hiçbir token tipi için geçerli değil",
  "code": "token_not_valid",
  "messages": [
    {
      "token_class": "AccessToken",
      "token_type": "access",
      "message": "Token is invalid"
    }
  ]
}
HTTP 401

### 3) Geçerli arşivle proje oluşturma
{
  "id": 1,
  "name": "Mağaza API",
  "description": "Örnek DRF projesi",
  "source_type": "ARCHIVE",
  "validation_status": "VALID",
  "archive": {
    "original_name": "magaza.zip",
    "size_bytes": 1555,
    "sha256": "912299109e391963348114a4dd3b609934507af6e67535d753fde46c2170476d",
    "uploaded_at": "2026-11-18T11:35:12.295957Z"
  },
  "validation_report": {
    "warnings": [],
    "checked_at": "2026-11-18T11:35:12+00:00",
    "django_apps": [
      "magaza/shop"
    ],
    "drf_detected": true,
    "schema_version": 1,
    "manage_py_found": true,
    "manage_py_paths": [
      "magaza/manage.py"
    ],
    "rejected_entries": [],
    "settings_modules": [
      "magaza/config/settings.py"
    ],
    "installed_apps_count": 4,
    "declared_settings_modules": [
      "config.settings"
    ]
  },
  "analysis_run_count": 0,
  "created_at": "2026-11-18T14:35:12.295957+03:00",
  "updated_at": "2026-11-18T14:35:12.295968+03:00"
}
HTTP 201

### 4) Liste
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Mağaza API",
      "description": "Örnek DRF projesi",
      "source_type": "ARCHIVE",
      "validation_status": "VALID",
      "archive": {
        "original_name": "magaza.zip",
        "size_bytes": 1555,
        "sha256": "912299109e391963348114a4dd3b609934507af6e67535d753fde46c2170476d",
        "uploaded_at": "2026-11-18T11:35:12.295957Z"
      },
      "validation_report": {
        "warnings": [],
        "checked_at": "2026-11-18T11:35:12+00:00",
        "django_apps": [
          "magaza/shop"
        ],
        "drf_detected": true,
        "schema_version": 1,
        "manage_py_found": true,
        "manage_py_paths": [
          "magaza/manage.py"
        ],
        "rejected_entries": [],
        "settings_modules": [
          "magaza/config/settings.py"
        ],
        "installed_apps_count": 4,
        "declared_settings_modules": [
          "config.settings"
        ]
      },
      "analysis_run_count": 0,
      "created_at": "2026-11-18T14:35:12.295957+03:00",
      "updated_at": "2026-11-18T14:35:12.295968+03:00"
    }
  ]
}
HTTP 200

### 5) Metadata güncelleme (PATCH)
{
  "id": 1,
  "name": "Mağaza API",
  "description": "Güncellenmiş açıklama",
  "source_type": "ARCHIVE",
  "validation_status": "VALID",
  "archive": {
    "original_name": "magaza.zip",
    "size_bytes": 1555,
    "sha256": "912299109e391963348114a4dd3b609934507af6e67535d753fde46c2170476d",
    "uploaded_at": "2026-11-18T11:35:12.295957Z"
  },
  "validation_report": {
    "warnings": [],
    "checked_at": "2026-11-18T11:35:12+00:00",
    "django_apps": [
      "magaza/shop"
    ],
    "drf_detected": true,
    "schema_version": 1,
    "manage_py_found": true,
    "manage_py_paths": [
      "magaza/manage.py"
    ],
    "rejected_entries": [],
    "settings_modules": [
      "magaza/config/settings.py"
    ],
    "installed_apps_count": 4,
    "declared_settings_modules": [
      "config.settings"
    ]
  },
  "analysis_run_count": 0,
  "created_at": "2026-11-18T14:35:12.295957+03:00",
  "updated_at": "2026-11-18T14:35:12.403320+03:00"
}
HTTP 200

### 6) Korumalı alan (owner) gönderme
{
  "owner": [
    "Bu alan istemci tarafından gönderilemez veya değiştirilemez."
  ]
}
HTTP 400

### 7) Başka kullanıcının projesine erişim (Bob → Alice'in projesi)
{
  "detail": "No Project matches the given query."
}
HTTP 404

### 8) Zip Slip arşivi
{
  "archive": [
    {
      "code": "PATH_TRAVERSAL",
      "detail": "Arşiv güvenli olmayan veya geçersiz girdiler içeriyor.",
      "entries": [
        {
          "path": "../../etc/cron.d/evil",
          "reason": "PATH_TRAVERSAL"
        }
      ]
    }
  ]
}
HTTP 400

### 9) Sembolik bağlantı
{
  "archive": [
    {
      "code": "SYMLINK",
      "detail": "Arşiv güvenli olmayan veya geçersiz girdiler içeriyor.",
      "entries": [
        {
          "path": "config/secret",
          "reason": "SYMLINK"
        }
      ]
    }
  ]
}
HTTP 400

### 10) Django projesi olmayan arşiv
{
  "archive": [
    {
      "code": "NO_DJANGO_SETTINGS",
      "detail": "Arşivde Django ayar modülü bulunamadı: INSTALLED_APPS içeren bir settings.py veya settings/ paketi gereklidir."
    }
  ]
}
HTTP 400

### 11) Sahte ZIP (uzantı .zip, içerik değil)
{
  "archive": [
    {
      "code": "NOT_A_ZIP",
      "detail": "Dosya içeriği geçerli bir ZIP arşivi değil."
    }
  ]
}
HTTP 400

### 12) Boyut sınırını aşan yükleme (sunucu sınırı 200000 bayt)
{
  "detail": "Yüklenen dosya en fazla 200000 bayt olabilir."
}
HTTP 413

### 13) JSON ile oluşturma denemesi
{
  "detail": "Proje oluşturma multipart/form-data ile yapılmalıdır."
}
HTTP 415

### 14) Silme

HTTP 204

### 15) Silinen proje
{
  "detail": "No Project matches the given query."
}
HTTP 404
```

Silmeden sonra özel depoda kalan dosya sayısı: 0.

## 3. PostgreSQL kaydı

API ile yeniden oluşturulan projenin `projects` tablosundaki kaydı (depolama adı yalnızca biçim
denetimiyle gösterilmiştir):

```text
 id |   owner    |    name    | source_type | validation_status | server_generated_name |    sha256    | original_name | size_bytes 
----+------------+------------+-------------+-------------------+-----------------------+--------------+---------------+------------
  2 | demo_alice | Mağaza API | ARCHIVE     | VALID             | t                     | 912299109e39 | magaza.zip    |       1555
(1 row)
```

Depodaki dosya ve izinleri (kök `PROJECT_ARCHIVE_ROOT` altında):

```text
600 storage/project_archives/2026/11/ea841f00bd864c269656857e6e0fd9fb.zip
```

## 4. Otomatik testler (PostgreSQL test veritabanı)

```text
$ python -m pytest -q core/tests/test_project_api.py core/tests/test_project_archive.py
147 passed in 24.88s

$ python -m pytest -q
350 passed in 72.38s (0:01:12)
```

Dosya başına test sayısı:

```text
     86 core/tests/test_project_api.py
     61 core/tests/test_project_archive.py
```

Ek doğrulamalar:

- Depo kökünden `python -m pytest -q backend`: 350 passed.
- Boşluk ve Türkçe karakter içeren bir yola kopyalanmış backend'de `python -m pytest -q`: 350 passed.
- Testler gerçek `backend/private_storage` dizinine yazmaz; her test kendi geçici arşiv kökünü kullanır.
- Statik tarama: `core/projects/`, `core/storage.py` ve temizlik komutunda `exec`, `eval`, `compile`,
  `__import__`, `import_module`, `subprocess`, `os.system`, `extractall`, `runpy`, `pickle` kullanımı yoktur.
