# H5-03 / #41 — Frontend–Backend–Veritabanı CRUD Entegrasyonu

React + Vite + TypeScript frontend'i Django REST Framework API'lerine bağlandı. Kimlik doğrulama, hesap
kilidi, şifre sıfırlama, proje CRUD, analiz kaydı ve referans gereksinim JSON işlemleri gerçek API ile
çalışır; veriler PostgreSQL'de saklanır. Kullanıcı sahipliği backend'de uygulanır ve iki kullanıcıyla
uçtan uca doğrulanmıştır.

## 1. Çalıştırma

Ön koşullar: PostgreSQL 16 (yerel), Python 3.13, Node.js ve npm. Docker Compose dosyası depoda
yoktur; yerel PostgreSQL kullanılır (`backend/.env.example`).

```bash
# Backend
cd backend
cp .env.example .env            # POSTGRES_* ve DJANGO_SECRET_KEY değerlerini doldurun (gerçek değerler repoya girmez)
pip install -r requirements.txt
python manage.py migrate
python manage.py check
python manage.py runserver 127.0.0.1:8000

# Frontend (ayrı terminal)
cd frontend
cp .env.example .env            # VITE_API_BASE_URL=http://127.0.0.1:8000
npm install
npm run dev                     # http://localhost:5173
```

Test kullanıcısı (gerçek kişisel veri kullanmayın; parolayı komut satırına yazmamak için etkileşimli):

```bash
cd backend
python manage.py shell -c "from django.contrib.auth import get_user_model; import getpass; u=get_user_model().objects.create_user('demo_kullanici', 'demo@example.test'); u.set_password(getpass.getpass()); u.save()"
```

### Ortam değişkenleri

| Değişken | Nerede | Açıklama |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `frontend/.env` | API taban adresi. Tarayıcıda görünür; gizli değer konmaz. |
| `CORS_ALLOWED_ORIGINS` | `backend/.env` | İzinli frontend kökenleri (varsayılan `http://localhost:5173,http://127.0.0.1:5173`; joker yok). |
| `JWT_ACCESS_MINUTES` / `JWT_REFRESH_DAYS` | `backend/.env` | Access 15 dk, refresh 7 gün (rotasyon + kara liste açık). |
| `AXES_FAILURE_LIMIT` / `AXES_COOLOFF_MINUTES` | `backend/.env` | 3 deneme / 15 dk kilit (değiştirilmedi). |
| `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS` | `backend/.env` | Şifre sıfırlama e-postası; üretimde SMTP. |
| `FRONTEND_PASSWORD_RESET_URL` | `backend/.env` | E-postadaki bağlantının frontend rotası (`/reset-password`). |
| `LOGIN_THROTTLE_RATE` | `backend/.env` | Anonim giriş isteği sınırı (varsayılan 10/dk). |

**CORS/CSRF:** Kimlik doğrulama yalnızca `Authorization: Bearer` başlığıyla yapılır; istemci çerez
göndermez (`credentials: 'omit'`), bu yüzden CSRF çerezi kullanılmaz. CORS yalnızca listelenen
kökenlere açıktır. Üretimde `DJANGO_DEBUG=false` ile HTTPS, HSTS ve güvenli çerez ayarları
(`backend/config/settings.py`) etkindir.

## 2. API entegrasyon matrisi

Hepsi `frontend/src/lib/api/client.ts` → `apiFetch` üzerinden gider. "Sahiplik" sütunu backend
denetimidir (`core/auth/permissions.py`: kullanıcıya göre süzülen queryset → başkasının kaydı **404**).

| İşlem | Yöntem ve uç nokta | Kimlik | Başarı / hata | Sahiplik | Ekran | Servis | Query key |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Giriş | `POST /api/auth/login/` | — | 200; 401; 429 kilit/sınır | — | Login | `auth.login` | — |
| Yenileme | `POST /api/auth/refresh/` | — | 200 (yeni access+refresh); 401 | — | (istemci) | `refreshAccessToken` | — |
| Çıkış | `POST /api/auth/logout/` | Bearer | 205; 400 | kendi token'ı | Kullanıcı menüsü | `logoutWithTokens` | önbellek temizlenir |
| Kullanıcı | `GET /api/auth/me/` | Bearer | 200; 401 | kendisi | Oturum, Profil | `getMe` | `['auth','me']` |
| Şifre talebi | `POST /api/auth/password-reset/` | — | 200 (her zaman genel); 400 | — | Şifremi unuttum | `requestPasswordReset` | — |
| Yeni parola | `POST /api/auth/password-reset/confirm/` | — | 200; 400 `token`/`new_password` | — | Şifre sıfırla | `confirmPasswordReset` | — |
| Proje oluştur | `POST /api/projects/` (multipart: `name`, `description`, `archive`) | Bearer | 201; 400 alan/`archive[{code}]`; 413; 415 | sahip sunucuda atanır | Yeni proje | `createProject` | `['projects']` geçersiz |
| Proje listesi | `GET /api/projects/?page=&page_size=` | Bearer | 200 sayfalı | yalnızca kendi | Projeler, Dashboard | `listProjects` | `['projects','list',p]` |
| Proje detay | `GET /api/projects/{id}/` | Bearer | 200; 404 | 404 | Proje detay | `getProject` | `['projects','detail',id]` |
| Proje güncelle | `PATCH /api/projects/{id}/` (`name`, `description`) | Bearer | 200; 400 (izinsiz alan); 404 | 404 | Düzenle | `updateProject` | `['projects']`, `['analysis-runs']` |
| Proje sil | `DELETE /api/projects/{id}/` | Bearer | 204; 409 aktif analiz; 404 | 404 | Silme onayı | `deleteProject` | listeden çıkarılır + geçersiz |
| Analiz oluştur | `POST /api/analysis-runs/` | Bearer | 201 (QUEUED); 400 `project`/`llm_model` | başkasının projesi 400 | Proje detay → Analizler | `createAnalysisRun` | `['analysis-runs']`, `['projects']` |
| Analiz listesi | `GET /api/analysis-runs/` | Bearer | 200 (dizi) | yalnızca kendi | Analizler, Dashboard | `listAnalysisRuns` | `['analysis-runs','list']` |
| Analiz detay | `GET /api/analysis-runs/{id}/` | Bearer | 200; 404 | 404 | Analiz özeti | `getAnalysisRun` | `['analysis-runs','detail',id]` (bitmemişse 15 sn yoklama) |
| Referans liste | `GET /api/reference-requirements/` | Bearer | 200 (dizi) | yalnızca kendi | Proje detay | `listReferenceRequirements` | `['reference-requirements','list']` |
| Referans ekle | `POST /api/reference-requirements/` | Bearer | 201; 400 (şema, metot, yinelenen kod, `project`) | başkasının projesi 400 | JSON yükle | `createReferenceRequirement` | geçersiz |
| Referans değiştir | `PUT /api/reference-requirements/{id}/` | Bearer | 200 (revision+1); 400; 404 | 404 | Düzenle | `replaceReferenceRequirement` | geçersiz |
| Referans kısmi | `PATCH /api/reference-requirements/{id}/` | Bearer | 200; 400; 404 | 404 | Etkinleştir/Pasifleştir | `patchReferenceRequirement` | geçersiz |
| Referans sil | `DELETE /api/reference-requirements/{id}/` | Bearer | 204; 404 | 404 | Sil | `deleteReferenceRequirement` | geçersiz |

Gerçek istek/yanıt örnekleri (hassas alanlar redakte): [`api-ornekleri.json`](api-ornekleri.json).
Tam şema: [`docs/api/openapi.yaml`](../../api/openapi.yaml).

## 3. Oturum ve JWT güvenliği

- **Saklama:** Access token yalnızca bellektedir. Refresh token, sayfa yenilemesinde oturumun sürmesi
  için `sessionStorage`'dadır: sekmeye özeldir ve sekme kapanınca silinir. Backend refresh token'ı
  JSON gövdede verdiği için HttpOnly çerez seçeneği bu sözleşmede yoktur.
  - XSS riski şu önlemlerle azaltılır: kısa access süresi, refresh rotasyonu + kara liste, çıkışta
    kara liste ve uygulamada HTML enjeksiyonu olmaması (`dangerouslySetInnerHTML` yok).
  - Token'lar URL'ye, konsola, hata mesajlarına ve kanıt dosyalarına yazılmaz.
- **Yenileme:** 401 alındığında tek seferlik (single-flight) refresh yapılır. Eş zamanlı 401'ler aynı
  yenilemeyi paylaşır ve istek en fazla bir kez yinelenir.
  - DRF kimlik doğrulaması görünümden önce çalıştığı için 401 alan istek sunucuda yan etki
    üretmemiştir; bu yüzden yinelemek çift kayıt oluşturmaz.
  - 403 hiçbir zaman yenileme tetiklemez. Refresh 401 dönerse oturum kapanır (sonsuz döngü olmaz).
    Ağ hatasında oturum korunur.
  - Çıkıştan önce başlamış bir yenilemenin yanıtı yok sayılır (`generation` sayacı).
- **Çıkış:**
  - Yerel oturum, token'lar ve tüm TanStack Query önbelleği hemen temizlenir; devam eden sorgular
    iptal edilir.
  - Refresh token `POST /api/auth/logout/` ile `keepalive` isteğiyle kara listeye alınır. Access
    süresi dolmuşsa önce bir kez yenilenir.
  - Kullanıcı değiştiğinde (giriş, çıkış, oturum sonu) önbellek temizlenir.
- **Korumalı rotalar:** Saklanan oturum sunucuda doğrulanırken (`status: checking`) korumalı içerik
  gösterilmez. Süresi dolmuş veya iptal edilmiş oturum "Oturum süreniz doldu" ekranına gider.
- **Hata eşlemesi:** `lib/api/errors.ts` 400, 401, 403, 404, 409, 413, 415, 429, 5xx, bağlantı hatası
  ve zaman aşımı için Türkçe mesaj üretir. 5xx gövdesi (stack trace) kullanıcıya iletilmez.

## 4. Hesap kilidi

- Kilit backend'dedir (django-axes, kullanıcı adı başına 3 deneme / 15 dk).
- H5-03'te kilit yanıtına `code: account_locked`, `locked_until`, `retry_after_seconds` ve
  `Retry-After` eklendi; `detail` korundu, geriye uyumludur. İstek sınırı 429'unda `code` yoktur.
- Frontend geri sayımı yalnızca sunucunun bildirdiği süreden gösterir; süre bildirilmezse geri sayım
  uydurmaz.
- Tarayıcı saati ileri alınsa da kilit sürer: kilit kararı sunucuda olduğu için E2E'de bu durumda
  giriş yine 429 ile reddedilir.

## 5. Şifre sıfırlama ve e-posta

- Talep her durumda aynı genel yanıtı döner; hesabın var olup olmadığı açığa çıkmaz.
- Bağlantı `FRONTEND_PASSWORD_RESET_URL?uid=…&token=…` biçimindedir. Frontend `uid`/`token`'ı okur,
  adres çubuğundan ve geçmişten siler. `referrer` politikası `same-origin`'dir.
- Geçersiz, süresi dolmuş ve daha önce kullanılmış bağlantılar sunucuda 400 ile reddedilir.
- **E2E e-posta doğrulaması:** Backend e-postayı gerçek SMTP protokolüyle yerel bir yakalayıcıya
  gönderir (`e2e/h5-03/smtp_catcher.py`, aiosmtpd). Bu, uygulamanın SMTP üzerinden gönderdiğini
  kanıtlar; dış dünyaya teslimat değildir ve üretim SMTP'si kullanılmamıştır.
  - Redakte e-posta: [`sifre-sifirlama-eposta.redakte.txt`](sifre-sifirlama-eposta.redakte.txt).
  - Birim testleri Django `locmem` backend'iyle yalnızca e-posta üretimini doğrular.

## 6. Proje, analiz ve referans gereksinim

- **Proje yükleme:** `FormData` ile gönderilir; boundary tarayıcı tarafından üretilir.
  - Arşiv güvenliği (path traversal, zip bomb, sembolik bağlantı, dosya sayısı) H4-03 backend
    denetimidir ve değiştirilmedi.
  - Gerçek ilerleme bilgisi alınamadığından yüzde gösterilmez; belirsiz "yükleniyor" durumu kullanılır.
  - Çift gönderim engellenir.
- **Silme:** Sunucu 204 döndükten sonra kayıt önbellekteki listelerden hemen çıkarılır. 409 (aktif
  analiz) durumunda kayıt kaldırılmaz. Analiz ve referans kayıtları CASCADE ile silinir.
- **AnalysisRun:**
  - Oluşturma yalnızca `QUEUED` kayıt açar; analiz motoru bu sürümde tetiklenmez ve arayüz bunu açıkça
    yazar.
  - Gerçek kayıt `/analyses/:id/summary` adresinde backend alanlarıyla (durum, ilerleme, anlık görüntü)
    gösterilir.
- **Referans JSON:**
  - Tek nesne veya dizi kabul edilir; `.json` dosyası seçilebilir.
  - İstemci ön doğrulaması (`features/requirements/referenceJson.ts`) şunları denetler: sözdizimi,
    zorunlu alanlar, tipler, kategori, `ACCESS_RULE` metodu (GET/POST/PUT/PATCH/DELETE; büyük harfe
    normalize edilir), durum kodları ve yinelenen kod. Asıl doğrulama sunucudadır; sunucu hataları
    alan yoluyla gösterilir.
  - GET/POST/PUT/PATCH/DELETE işlemlerinin tamamı arayüzde vardır.

## 7. Gerçek ve DEMO ayrımı

| Gerçek (API + PostgreSQL) | DEMO (yalnızca `/demo/analyses`, "DEMO" etiketli) |
| --- | --- |
| Kullanıcı, JWT, projeler, analiz kayıtları, referans gereksinimler, dashboard sayıları | Endpoint analizi, Pytest üretimi, canlı test yürütme ve tahmini süre, model/fallback, güvenlik bulguları, PDF/JSON rapor ve metrikler |

- Backend'e ulaşılamazsa DEMO'ya geçilmez; hata gösterilir.
- Gerçek analiz kimliği örnek sonuçlarla eşleştirilmez; gerçek kayıtta sonuç sekmeleri "henüz bağlı
  değil" der.
- DEMO önbelleği ayrı anahtar alanındadır (`['demo', …]`).

## 8. Testler

| Paket | Komut | Sonuç |
| --- | --- | --- |
| Frontend birim/bileşen (sahte HTTP backend'i, gerçek istemci kodu) | `cd frontend && npm test` | 37 dosya / 252 test (başlangıç 32 / 185) |
| Frontend tip denetimi / derleme | `npm run typecheck`, `npm run build` | Başarılı |
| Backend (PostgreSQL test veritabanı) | `cd backend && python -m pytest -q` | 471 test (başlangıç 439) |
| H5-03 backend entegrasyonu | `python -m pytest -q core/tests/test_h5_03_integration.py core/tests/test_h5_03_lockout_info.py` | 32 test |
| Gerçek uçtan uca (Chromium + Vite + DRF + PostgreSQL + SMTP) | `bash e2e/h5-03/run.sh` | 30 senaryo, [`e2e-sonuclari.json`](e2e-sonuclari.json) |

- Lint betiği/ESLint ve frontend CI workflow'u depoda yoktur; bu yüzden çalıştırılmadı.
- E2E ortam ayarları ve test kullanıcılarının güvenli oluşturulması: [`e2e/h5-03/README.md`](../../../e2e/h5-03/README.md).

**Değiştirilen eski frontend testleri ve gerekçeleri:**

| Test | Gerekçe |
| --- | --- |
| Login | Etiket "Kullanıcı adı" oldu (backend `username` alır); kilit yanıtı artık sunucudan kalan süre içerir; mock sabitleri `src/test/fake-api.ts`'e taşındı. |
| ProtectedRoute | `signInMock` kaldırıldı; yerine oturum doğrulanırken içerik gizleme ve iptal edilmiş oturum testleri eklendi. |
| Profile | Sahte başarı gösteren parola formu kaldırıldı (backend uç noktası yok); yönlendirme testi eklendi. |
| Overview | Gerçek analizlere örnek bulgu eşlemesi kaldırıldı; "Örnek veri" etiketi gerçek veriyi yanlış tanıttığı için test güncellendi. |
| AnalysisScreens | H5-02 ekranları `/demo/analyses` rotalarına taşındı; gerçek kayıt testleri eklendi. |
| projects.test (413) | jsdom FormData'sı sahte `size` özelliğini kopyalamadığı için sunucunun 413 yanıtının iletilmesi test ediliyor. |

**Silinen testler:** Yalnızca Profil'deki sahte başarı formunun 6 testi, form kaldırıldığı için
silindi. Bunun dışında hiçbir test silinmedi veya atlanmadı.

## 9. Backend değişiklikleri

| Değişiklik | Dosya | Gerekçe ve etki |
| --- | --- | --- |
| Kilit yanıtına kalan süre | `core/auth/exceptions.py`, `serializers.py`, `views.py` | Issue #41: "varsa kalan süre bilgisini göster". Alan eklemesi; `detail` aynı, geriye uyumlu. Kilit kararı değişmedi. |
| OpenAPI 429 şeması/örneği | `core/api/schema.py`, `docs/api/openapi.*`, `docs/api/authentication.md` | Sözleşme belgesi güncel tutuldu; `test_openapi.py` yeni alanları doğruluyor. |

Model, migration, izin ve sahiplik kodu değiştirilmedi.

## 10. Kanıtlar

| Kanıt | Yol |
| --- | --- |
| Ekran görüntüleri (gerçek uygulama) | [`docs/mockup/h5-03/`](../../mockup/h5-03/) — 01–17 |
| E2E sonuçları | [`e2e-sonuclari.json`](e2e-sonuclari.json) |
| Gerçek API istek/yanıt örnekleri | [`api-ornekleri.json`](api-ornekleri.json) |
| SMTP ile gönderilen sıfırlama e-postası (redakte) | [`sifre-sifirlama-eposta.redakte.txt`](sifre-sifirlama-eposta.redakte.txt) |
| PostgreSQL doğrulama yardımcısı | [`e2e/h5-03/db_probe.py`](../../../e2e/h5-03/db_probe.py) |

## 11. Bilinen sınırlılıklar

- Analiz motoru (AST, LLM, sandbox, tarama) çalıştırılmaz; analiz kayıtları `QUEUED` kalır. E2E'de
  silme senaryosu için analizin sonlanması `db_probe.py finish-run` ile simüle edilmiştir.
- Sonuç ekranları ve PDF/JSON rapor uç noktaları backend'de yoktur. PDF düğmesi pasif ve açıklamalı
  kalır; DEMO JSON gerçek rapor gibi sunulmaz.
- Oturum içi parola değiştirme uç noktası yoktur.
- Refresh token `sessionStorage`'dadır: XSS'e karşı HttpOnly çerez kadar güçlü değildir; HttpOnly
  çerez için backend sözleşmesinin değişmesi gerekir.
- Analiz ve referans listelerinde sayfalama yoktur (backend sözleşmesi).
- Docker Compose yapılandırması depoda yoktur.

## 12. H5-06 canlı demo için devir

1. PostgreSQL'i başlatın, `backend/.env` ve `frontend/.env` dosyalarını hazırlayın, ardından §1'deki
   komutları çalıştırın.
2. Demo kullanıcısını §1'deki etkileşimli komutla oluşturun.
3. Akış: Giriş → Yeni proje (örnek ZIP: `python e2e/h5-03/make_fixtures.py --out /tmp/fx`) → Proje
   detay → Referans JSON yükle → Analiz başlat → Analiz özeti.
4. Sonuç ekranları yalnızca **DEMO analiz örnekleri** bağlantısında gösterilmelidir; gerçek kayıt
   olarak sunulmamalıdır.
5. Hesap kilidi göstermek için ayrı bir demo kullanıcısıyla 3 hatalı deneme yapın. Kilit 15 dakika
   sürer; demo kullanıcınızı kilitlemeyin.
