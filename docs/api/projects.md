# Proje Yükleme ve Yönetimi

Tüm işlemler JWT ister. Kullanıcı yalnızca kendi projelerini görür; başkasına ait proje kimliği **404** döner.

## 1. Proje oluşturma — `POST /api/projects/` (etiket: Proje Yükleme)

İstek gövdesi **`multipart/form-data`** olmalıdır; JSON veya başka içerik türü **415** döner
(`{"detail": "Proje oluşturma multipart/form-data ile yapılmalıdır."}`).

| Alan | Tür | Zorunlu | Not |
|---|---|---|---|
| `name` | metin | evet | Kullanıcı içinde tekil |
| `description` | metin | hayır | |
| `archive` | dosya (`string`/`binary`) | evet | Tek bir `.zip`; birden fazla dosya 400 |

`owner`, `source_archive`, `archive_sha256`, `validation_status` vb. alanlar istemciden alınmaz; gönderilirse
**400** ile reddedilir (sessizce yok sayılmaz). Sahip sunucuda oturumdaki kullanıcıdır.

```bash
curl -X POST "$BASE_URL/api/projects/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F name="Mağaza API" -F description="örnek" -F archive=@magaza.zip
```

**201** yanıtı `Project` bileşenidir: `id`, `name`, `description`, `source_type`, `validation_status`,
`archive` (`original_name`, `size_bytes`, `sha256`, `uploaded_at`), `validation_report`, `analysis_run_count`,
`created_at`, `updated_at`. Sunucudaki depolama yolu yanıtta **yer almaz**.

Yüklenen kod çalıştırılmaz, içe aktarılmaz ve diske açılmaz; arşiv yalnızca okunarak doğrulanır.

### 400 ile 413 farkı

- **413** — boyut sınırını (`max_upload_bytes`, varsayılan 50 MiB) aşan yükleme, gövde okunurken durdurulur:
  `{"detail": "Yüklenen dosya en fazla 52428800 bayt olabilir."}` (sayı yapılandırmaya bağlıdır).
- **400** — gövde kabul edilip içeriği doğrulandıktan sonra reddedilen arşiv. Biçim:

```json
{"archive": [{"code": "PATH_TRAVERSAL", "detail": "Arşiv güvenli olmayan veya geçersiz girdiler içeriyor.",
              "entries": [{"path": "../evil.py", "reason": "PATH_TRAVERSAL"}]}]}
```

`code` değerleri (`ArchiveErrorCodeEnum`): `UNSUPPORTED_TYPE`, `EMPTY_FILE`, `NOT_A_ZIP`, `CORRUPT_ARCHIVE`,
`UNSUPPORTED_COMPRESSION`, `ENCRYPTED`, `EMPTY_ARCHIVE`, `FILE_TOO_LARGE`, `TOO_MANY_ENTRIES`, `PATH_TRAVERSAL`,
`BACKSLASH_PATH`, `ABSOLUTE_PATH`, `DRIVE_PATH`, `UNC_PATH`, `INVALID_NAME`, `RESERVED_NAME`, `SYMLINK`,
`SPECIAL_FILE`, `DUPLICATE_PATH`, `CASE_COLLISION`, `PATH_CONFLICT`, `PATH_TOO_LONG`, `TOO_DEEP`,
`MEMBER_TOO_LARGE`, `UNCOMPRESSED_TOO_LARGE`, `COMPRESSION_RATIO`, `NO_DJANGO_SETTINGS`, `NO_DJANGO_ENTRYPOINT`,
`UNSAFE_ARCHIVE`. `entries[].reason` ayrıca `CORRUPT_MEMBER` olabilir.

Varsayılan sınırlar (ortam değişkenleriyle değiştirilebilir, bkz. `backend/docs/h4_03_project_api.md` §4):
arşiv ≤ 50 MiB, açılmış toplam ≤ 200 MiB, tek dosya ≤ 20 MiB, ≤ 10 000 girdi, derinlik ≤ 32, yol ≤ 240 karakter,
sıkıştırma oranı ≤ 100. Şemadaki işlem açıklaması bu değerleri yapılandırmadan üretir.

**429** — kullanıcı başına yükleme sınırı (`PROJECT_UPLOAD_THROTTLE_RATE`, varsayılan 30/saat).

## 2. Listeleme ve detay (etiket: Proje Yönetimi)

- `GET /api/projects/` — sayfalıdır (`PaginatedProjectList`: `count`, `next`, `previous`, `results`);
  `page` ve `page_size` (en fazla 100, varsayılan 20) sorgu parametreleri. En yeni proje önce gelir.
- `GET /api/projects/{id}/` — `Project`; bulunamazsa / başkasınınsa **404**
  `{"detail": "No Project matches the given query."}` (DRF'nin varsayılan İngilizce metni).

## 3. Güncelleme — `PUT` / `PATCH /api/projects/{id}/`

Yalnızca `name` ve `description` güncellenebilir (JSON veya multipart). Arşiv değiştirilemez (dosya gönderilirse
400); korumalı alan gönderimi 400; aynı adlı başka projeniz varsa
`{"name": ["Bu adla kayıtlı bir projeniz zaten var."]}`.

## 4. Silme — `DELETE /api/projects/{id}/`

**204** (gövde yok); proje, bağlı analiz kayıtları ve saklanan arşiv silinir. Projede aktif durumda
(QUEUED, ANALYZING, GENERATING, VALIDATING, EXECUTING, SCANNING) analiz varsa **409**:
`{"detail": "Projenin devam eden bir analizi var; analiz bitmeden proje silinemez."}`.
