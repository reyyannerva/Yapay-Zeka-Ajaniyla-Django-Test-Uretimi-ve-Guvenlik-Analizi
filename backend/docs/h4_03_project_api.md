# Proje Yönetimi ve Güvenli Arşiv Yükleme API'si (H4-03 / Issue #35)

Kullanıcılar Django/DRF projelerini ZIP arşivi olarak yükler, kendi projelerini listeler, görüntüler, ad ve
açıklamasını günceller ve siler. Yüklenen kaynak kod **çalıştırılmaz, içe aktarılmaz, kurulmaz ve diske
açılmaz**; arşiv doğrulandıktan sonra olduğu gibi özel bir depoda saklanır ve sonraki analiz aşamalarına
hazır bekler.

Kod: `backend/core/projects/` · Depolama: `backend/core/storage.py` · Testler:
`backend/core/tests/test_project_api.py`, `test_project_archive.py` · Gerçek istek-yanıt kanıtı:
[`evidence/h4_03_project_api.md`](evidence/h4_03_project_api.md).

## 1. Uç noktalar

Tüm uç noktalar kimlik doğrulama gerektirir: `Authorization: Bearer <access token>` (SimpleJWT, H4-02 —
token `POST /api/auth/login/` ile alınır).

| Yöntem | URL | Amaç | Gövde | Başarılı yanıt |
|---|---|---|---|---|
| `POST` | `/api/projects/` | Arşiv yükleyerek proje oluşturma | `multipart/form-data`: `name` (zorunlu), `description` (isteğe bağlı), `archive` (zorunlu, .zip) | `201` |
| `GET` | `/api/projects/` | Kullanıcının projelerini listeleme (yeniden eskiye, sayfalı: `?page=`, `?page_size=` ≤ 100) | — | `200` |
| `GET` | `/api/projects/{id}/` | Proje detayı | — | `200` |
| `PATCH` | `/api/projects/{id}/` | Ad ve/veya açıklama güncelleme | JSON: `name`, `description` | `200` |
| `PUT` | `/api/projects/{id}/` | Ad ve açıklamayı birlikte güncelleme (`name` zorunlu) | JSON | `200` |
| `DELETE` | `/api/projects/{id}/` | Projeyi, bağlı analiz kayıtlarını ve arşivi silme | — | `204` |

Hata kodları:

| Kod | Ne zaman |
|---|---|
| `400` | Geçersiz alan, korumalı alan gönderme, aynı adlı proje, geçersiz/güvensiz/Django olmayan arşiv |
| `401` | Token yok, geçersiz, süresi dolmuş veya kullanıcı devre dışı |
| `404` | Proje yok **veya başka kullanıcıya ait** (varlığı ifşa edilmez) |
| `405` | Desteklenmeyen yöntem (ör. liste üzerinde `PUT`/`DELETE`) |
| `409` | Silinmek istenen projenin devam eden (aktif) bir analizi var |
| `413` | Yüklenen dosya boyut sınırını aşıyor |
| `415` | Proje oluşturma `multipart/form-data` dışında bir içerik türüyle gönderildi |
| `429` | Kullanıcı başına yükleme sınırı aşıldı (`PROJECT_UPLOAD_THROTTLE_RATE`, varsayılan `30/hour`) |

## 2. Örnekler

Token alma (değerler örnektir; gerçek token belgeye yazılmaz):

```bash
curl -s -X POST http://127.0.0.1:8000/api/auth/login/ -H 'Content-Type: application/json' -d '{"username":"alice","password":"<parola>"}'
```

Proje oluşturma:

```bash
curl -X POST http://127.0.0.1:8000/api/projects/ -H "Authorization: Bearer $ACCESS" -F "name=Mağaza API" -F "description=Örnek DRF projesi" -F "archive=@magaza.zip;type=application/zip"
```

Başarılı yanıt (`201`, kısaltılmış; gerçek çıktı kanıt dosyasında):

```json
{
  "id": 1,
  "name": "Mağaza API",
  "description": "Örnek DRF projesi",
  "source_type": "ARCHIVE",
  "validation_status": "VALID",
  "archive": {"original_name": "magaza.zip", "size_bytes": 1555, "sha256": "9122…476d", "uploaded_at": "2026-11-18T14:35:37+03:00"},
  "validation_report": {
    "schema_version": 1, "manage_py_found": true, "manage_py_paths": ["magaza/manage.py"],
    "settings_modules": ["magaza/config/settings.py"], "declared_settings_modules": ["config.settings"],
    "django_apps": ["magaza/shop"], "installed_apps_count": 4, "drf_detected": true,
    "rejected_entries": [], "warnings": [], "checked_at": "2026-11-18T11:35:12+00:00"
  },
  "analysis_run_count": 0,
  "created_at": "2026-11-18T14:35:37+03:00",
  "updated_at": "2026-11-18T14:35:37+03:00"
}
```

Güvensiz arşiv (`400`):

```json
{"archive": [{"code": "PATH_TRAVERSAL", "detail": "Arşiv güvenli olmayan veya geçersiz girdiler içeriyor.",
              "entries": [{"path": "../../etc/cron.d/evil", "reason": "PATH_TRAVERSAL"}]}]}
```

Kimlik doğrulamasız istek (`401`):

```json
{"detail": "Giriş bilgileri verilmedi."}
```

Güncelleme ve silme:

```bash
curl -X PATCH http://127.0.0.1:8000/api/projects/1/ -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' -d '{"description":"Güncellenmiş açıklama"}'
```

```bash
curl -X DELETE http://127.0.0.1:8000/api/projects/1/ -H "Authorization: Bearer $ACCESS"
```

## 3. Sahiplik ve korumalı alanlar

* Liste ve detay H4-02 `OwnedQuerysetMixin` ile `owner = request.user` olarak süzülür. Başka kullanıcının
  projesine yapılan `GET`/`PATCH`/`PUT`/`DELETE` istekleri **404** döner; ad, dosya adı, özet veya analiz
  sayısı gibi hiçbir bilgi sızmaz. (Veri sözlüğü 13.1 403 önerir; H4-02'de birleştirilmiş davranış bilgi
  gizleyen 404'tür ve burada aynen kullanılır.)
* Sahip her zaman sunucu tarafında atanır. İstemcinin gönderdiği `owner`, `id`, `source_type`,
  `source_archive`, `archive_sha256`, `validation_status`, `validation_report`, `created_at` gibi alanlar
  **sessizce yok sayılmaz, 400 ile reddedilir** (toplu atama koruması).
* Yanıtlar depolama anahtarını (`source_archive`), sunucu dosya adını veya mutlak yolu içermez; arşiv için
  yalnızca özgün dosya adı (yalnızca görüntüleme amaçlı), boyut, SHA-256 ve yükleme zamanı döner.
* Arşiv bu sürümde değiştirilemez; güncelleme isteğinde dosya gönderilirse 400 döner (yeni arşiv için
  yeni proje oluşturulur).

## 4. Yükleme sınırları ve yapılandırma

Bu sınırlar proje kararıdır (isterlerde sayısal değer tanımlı değildir); `backend/.env` veya ortam
değişkenleriyle değiştirilebilir.

| Ayar (ortam değişkeni) | Varsayılan | Anlamı |
|---|---|---|
| `PROJECT_UPLOAD_MAX_BYTES` | 50 MiB | Sıkıştırılmış arşiv boyutu |
| `PROJECT_UPLOAD_MAX_UNCOMPRESSED_BYTES` | 200 MiB | Açılmış toplam boyut |
| `PROJECT_UPLOAD_MAX_MEMBER_BYTES` | 20 MiB | Tek dosyanın açılmış boyutu |
| `PROJECT_UPLOAD_MAX_ENTRIES` | 10 000 | Girdi sayısı |
| `PROJECT_UPLOAD_MAX_DEPTH` | 32 | Dizin derinliği |
| `PROJECT_UPLOAD_MAX_PATH_LENGTH` | 240 karakter | Girdi yolu uzunluğu |
| `PROJECT_UPLOAD_MAX_COMPRESSION_RATIO` | 100 | Açılmış / sıkıştırılmış oranı (girdi başına ve toplam) |
| `PROJECT_UPLOAD_RATIO_MIN_BYTES` | 1 MiB | Oran denetiminin uygulandığı en küçük açılmış boyut |
| `PROJECT_UPLOAD_THROTTLE_RATE` | `30/hour` | Kullanıcı başına yükleme isteği |
| `PROJECT_ARCHIVE_ROOT` | `backend/private_storage` | Özel arşiv deposu kökü |

Boyut sınırı üç katmanda uygulanır:

1. `Content-Length` başlığı sınırı (64 KiB çok parçalı form payı dışında) açıkça aşıyorsa istek gövde
   okunmadan 413 ile reddedilir.
2. Gövde akarken `MaxSizeUploadHandler` her parçayı sayar ve sınır aşıldığında yüklemeyi durdurur
   (geçici dosyaya fazladan veri yazılmaz) → 413.
3. Doğrulayıcı dosyanın gerçek boyutunu yeniden ölçer.

Uygulama katmanı, gövdenin sunucuya ulaşmasını engelleyemez. Üretimde ters vekil sunucuda da (ör. nginx
`client_max_body_size`) aynı sınır tanımlanmalıdır (H8 dağıtım).

## 5. Desteklenen biçim ve arşiv güvenlik denetimleri

Yalnızca **ZIP** desteklenir. Uzantı `.zip` olmalı **ve** içerik ZIP imzasıyla başlamalıdır; istemcinin
gönderdiği MIME türüne güvenilmez. Arşiv hiçbir zaman diske açılmaz. Merkez dizin okunur, her dosya bellekte
sınırlı parçalarla açılıp sayılır.

| Denetim | Ret kodu |
|---|---|
| Boş dosya / uzantı / ZIP olmayan içerik | `EMPTY_FILE`, `UNSUPPORTED_TYPE`, `NOT_A_ZIP` |
| Bozuk, kesik arşiv; CRC uyuşmazlığı | `CORRUPT_ARCHIVE` |
| Desteklenmeyen sıkıştırma; şifreli girdi | `UNSUPPORTED_COMPRESSION`, `ENCRYPTED` |
| Hiç girdi yok | `EMPTY_ARCHIVE` |
| `..` ile yol geçişi (Zip Slip; normalleştirme sonrası da) | `PATH_TRAVERSAL` |
| Ters eğik çizgi içeren yol | `BACKSLASH_PATH` |
| Mutlak yol, sürücü harfi (`C:`), UNC (`//sunucu`) | `ABSOLUTE_PATH`, `DRIVE_PATH`, `UNC_PATH` |
| Denetim karakteri, `<>:"\|?*`, sonu nokta/boşluk; Windows ayrılmış adları (`CON`, `NUL`, `COM1`…) | `INVALID_NAME`, `RESERVED_NAME` |
| Sembolik bağlantı; FIFO, aygıt, soket | `SYMLINK`, `SPECIAL_FILE` |
| Yinelenen yol; büyük/küçük harf duyarsız çakışma; aynı yolun hem dosya hem dizin olması | `DUPLICATE_PATH`, `CASE_COLLISION`, `PATH_CONFLICT` |
| Girdi sayısı, derinlik, yol uzunluğu | `TOO_MANY_ENTRIES`, `TOO_DEEP`, `PATH_TOO_LONG` |
| Dosya / toplam açılmış boyut (bildirilen boyuta güvenilmez, gerçek okuma sayılır) | `MEMBER_TOO_LARGE`, `UNCOMPRESSED_TOO_LARGE`, `FILE_TOO_LARGE` |
| Sıkıştırma oranı (ZIP bombası) | `COMPRESSION_RATIO` |

Hassas dosyalar (`.env`, `.env.*`, `*.pem`, `*.key`, `id_rsa`…) arşivi reddettirmez. Bu dosyalar
`validation_report.rejected_entries` içinde `SECRET_FILE_EXCLUDED` olarak listelenir; ileride arşiv
açılırken atlanmaları gerekir. İçerikleri hiçbir yanıta veya kayda yazılmaz.

## 6. Django/DRF yapı ön kontrolü

Kaynak çalıştırılmaz. Yalnızca küçük metin dosyaları (≤ 256 KiB) okunur ve `ast.parse` ile ayrıştırılır;
ayrıştırma kodu çalıştırmaz. Kabul kuralı:

1. `INSTALLED_APPS` tanımı içeren en az bir ayar modülü (`settings.py` veya `settings/` paketindeki bir
   modül) bulunmalı → yoksa `NO_DJANGO_SETTINGS`.
2. En az bir giriş noktası (`manage.py`, `wsgi.py`, `asgi.py` veya `urls.py`) bulunmalı → yoksa
   `NO_DJANGO_ENTRYPOINT`.

Kök dizin ve uygulama adları serbesttir; iç içe yapılar (ör. `kaynak/backend/manage.py`) desteklenir. DRF
zorunlu değildir: `rest_framework` INSTALLED_APPS'te veya bağımlılık dosyalarında (`requirements*.txt`,
`pyproject.toml`, `Pipfile`, `setup.cfg`, `setup.py`) aranır, bulunmazsa uyarı verilir. Bu kontrol
yalnızca bir uygunluk ön kontrolüdür; projenin çalışabilir veya güvenli olduğunu kanıtlamaz.

## 7. Özel depolama ve dosya yaşam döngüsü

* Arşivler `PROJECT_ARCHIVE_ROOT` altında, `MEDIA_ROOT` ve statik dizinlerden ayrı tutulur ve hiçbir URL
  ile sunulmaz (`ProjectArchiveStorage.url()` bilinçli olarak desteklenmez). İzinler POSIX'te dosya 0600,
  dizin 0700'dür.
* Depolama adı sunucu tarafından üretilir: `project_archives/YYYY/MM/<32 onaltılık>.zip`. İstemci dosya
  adı yol olarak hiçbir zaman kullanılmaz. Farklı kullanıcıların aynı adlı dosyaları birbirinin üzerine
  yazılamaz.
* **Oluşturma:** Arşiv önce tamamen doğrulanır (depoya yazılmadan). Sonra depoya yazılır ve kayıt
  kaydedilir. Kayıt başarısız olursa (ör. eşzamanlı aynı ad) yazılan dosya hemen silinir.
* **Güncelleme:** Yalnızca `name` ve `description` değişir; arşiv, özet ve doğrulama raporu korunur.
* **Silme:** Aktif analizi (`QUEUED`…`SCANNING`) olan proje silinemez (409). Diğer durumlarda proje ve
  CASCADE ile bağlı kayıtlar (gereksinimler, analiz çalıştırmaları, endpoint'ler, testler, denemeler,
  bulgular, raporlar, LLM çağrıları; veri sözlüğü 12.1) silinir. Bu, analiz sonuçlarının da kalıcı olarak
  silinmesi demektir. Arşiv dosyası yalnızca veritabanı işlemi başarıyla tamamlandıktan sonra
  (`transaction.on_commit`) silinir; işlem geri alınırsa dosya korunur.
* **Temizlik hatası:** Dosya silinemezse (ör. dosya kilitli) kayıt zaten silinmiştir; olay `WARNING`
  düzeyinde günlüğe yazılır ve dosya "öksüz" kalır. Öksüz dosyalar şu komutla listelenir, `--delete` ile
  silinir:

```bash
cd backend && python manage.py cleanup_project_archives
```

* Gelecekte bir indirme uç noktası gerekirse yalnızca kimlik doğrulamalı ve sahiplik denetimli olmalıdır;
  herkese açık indirme bağlantısı eklenmemelidir.

## 8. PostgreSQL

Şema değişikliği yoktur. Migration `core.0002_project_archive_private_storage` yalnızca alanın depolama
arka ucunu (`ProjectArchiveStorage`) kaydeder; `sqlmigrate core 0002` çıktısı `-- (no-op)`'tur. Kurulum ve
doğrulama komutları `backend/README.md` bölüm 1–3'tedir.

## 9. Testler

```bash
cd backend && python -m pytest -q core/tests/test_project_api.py core/tests/test_project_archive.py
```

```bash
cd backend && python -m pytest -q
```

## 10. Bilinen sınırlar ve ertelenenler

* Arşiv değiştirme uç noktası yoktur. `ALLOWED_DIRECTORY` kaynaklı projeler API'den oluşturulamaz;
  bunun için izinli kök dizin yapılandırması gerekir ve bu sonraki bir iş kalemidir.
* Arşiv açma (çalışma dizinine güvenli çıkarma) analiz aşamasının işidir (H6). Bu aşamada
  `rejected_entries` listesine uyulmalı ve aynı yol denetimleri yeniden uygulanmalıdır.
* Silme ile yeni analiz başlatma arasındaki yarış satır kilidiyle engellenmez. Analiz başlatma servisi
  (H4-04) projeyi `select_for_update()` ile kilitlemelidir.
* Rapor dosyası üretimi henüz yoktur; proje silindiğinde rapor dosyalarının temizliği rapor üretimi
  eklendiğinde (H6) uygulanmalıdır.
* Ters vekil sunucu düzeyindeki boyut sınırı dağıtım aşamasında (H8) yapılandırılmalıdır.

## 11. Güvenlik incelemesi

| Risk | Durum | Önlem / kanıt |
|---|---|---|
| Nesne düzeyi yetkilendirme (BOLA) | Giderildi | Sahibe göre süzülmüş queryset; başkasının projesine GET/PATCH/PUT/DELETE → 404 (iki kullanıcıyla test) |
| Kimlik doğrulama | Giderildi | SimpleJWT (H4-02); eksik/geçersiz/süresi dolmuş token ve devre dışı kullanıcı → 401 |
| Toplu atama | Giderildi | İzin verilmeyen alanlar 400 ile reddedilir; sahip sunucuda atanır |
| Yol geçişi (Zip Slip), mutlak/sürücü/UNC yolları | Giderildi | Arşiv açılmaz; girdi adları normalleştirilip reddedilir |
| Sembolik bağlantı ve özel dosyalar | Giderildi | Unix mod bitlerinden tespit edilip reddedilir |
| ZIP bombası / kaynak tüketimi | Azaltıldı | Gerçek açılmış boyut sayılır; oran, girdi, derinlik, boyut sınırları; kullanıcı başına yükleme sınırı. Doğrulama 200 MiB'a kadar CPU harcayabilir |
| Yüklenen kodun çalıştırılması | Giderildi | Kod içe aktarılmaz, çalıştırılmaz; yan etkili yük içeren arşivle test edildi |
| Hassas veri ifşası (depolama yolu, sırlar) | Giderildi | Yanıtta depolama anahtarı/mutlak yol yok; `.env` içeriği okunmaz, yalnızca adı raporlanır |
| Herkese açık dosya erişimi | Giderildi | Özel depo, URL yok, 0600 izinleri |
| Dosya üzerine yazma | Giderildi | Sunucu üretimli UUID adları; istemci adı yol olarak kullanılmaz |
| Dosya ↔ veritabanı tutarsızlığı | Azaltıldı | Başarısız oluşturmada dosya silinir; silme `on_commit` sonrası. Depo silme hatası günlüğe yazılır ve `cleanup_project_archives` ile temizlenir |
| Boyut sınırının gövde alınmadan uygulanması | Azaltıldı | `Content-Length` ön kontrolü ve akış sırasında durdurma. Ters vekil sunucu sınırı H8'e ertelendi |
| Hata iletilerinden bilgi sızması | Giderildi | Ret kodları ve kısa açıklama; yığın izi/yol dönmez (testle doğrulandı) |
| Silme–analiz başlatma yarışı | Ertelendi | H4-04 analiz başlatma servisi projeyi `select_for_update()` ile kilitlemeli |
| Arşivin sonradan açılması (çıkarma) | Ertelendi | H6 analiz aşaması; aynı yol denetimleri ve `rejected_entries` uygulanmalı |

Bu inceleme ve testler sistemin tamamen güvenli olduğunu kanıtlamaz; tanımlı tehditlere karşı uygulanan
önlemleri ve doğrulamalarını belgeler.
