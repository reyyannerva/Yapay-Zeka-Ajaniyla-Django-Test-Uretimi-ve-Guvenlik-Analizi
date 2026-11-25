# H5-06 / Issue #44 — Frontend entegrasyon kontrolü ve canlı demo

Bu belge Hafta 5 canlı demosunun akışını, kurulumunu, ön kontrol listesini, gerçek ve prototip özellik
ayrımını ve demo provasının kanıtlarını içerir. Tüm kanıtlar gerçek ortamda üretilmiştir: Chromium, Vite
frontend, Django/DRF backend, PostgreSQL 16 ve yerel SMTP yakalayıcı. API taklit edilmemiştir.

## 1. Demo akışı (önerilen sıra, ~8 dk)
| # | Adım | Ekran | Ne gösterilir | Kanıt |
|---|---|---|---|---|
| 1 | Giriş | `/login` | SimpleJWT ile gerçek giriş | `screenshots/01-giris.png` |
| 2 | Dashboard | `/dashboard` | Gerçek API verisi; "Örnek veri" etiketi yok | `02-dashboard.png` |
| 3 | Proje yükleme | `/projects/new` | Güvenli örnek ZIP, multipart; PostgreSQL kaydı | `03-proje-yukleme.png` |
| 4 | Proje listesi ve detay | `/projects`, `/projects/:id` | Kullanıcının kendi projeleri | `04-proje-listesi.png`, `05-proje-detay.png` |
| 5 | Referans JSON | Proje detayı → Referans gereksinimler | GET, POST, PUT, PATCH ve DELETE gereksinimleri doğrulanıp kaydedilir | `06-referans-json-5-metot.png` |
| 6 | Analiz kaydı | Proje detayı → Analiz başlat | Gerçek AnalysisRun (QUEUED); sonuç servisleri "henüz bağlı değil" | `07-analiz-kaydi.png`, `08-gercek-analiz-sonuc-servisi-bagli-degil.png` |
| 7 | Deney sonuçları | `/experiments` | H5-05 çevrimdışı karşılaştırması: üç yöntem, iki katman, gerçek ölçümler | `09-deney-sonuclari.png`, `13-mobil-deney-sonuclari.png` |
| 8 | (İsteğe bağlı) DEMO ekranları | `/demo/analyses` | Henüz backend'i olmayan analiz, test, bulgu ve rapor ekranları; DEMO etiketli | `10-12-*.png` |
| 9 | Çıkış | Kullanıcı menüsü | Oturum kapanır, korumalı sayfa girişe yönlendirir | demo provası D-09 |

**Anlatım notu:** "Deney sonuçları" ekranındaki değerler canlı analiz sonucu değildir. Bunlar H5-05'in
(#43) geliştirme kümesi ölçümleridir. Katman A'da F1 "Ölçülemedi" olarak gösterilir, çünkü bilinen kusur
yoktur. Katman B'deki F1 = 1,00 yalnızca 3 kusurlu kontrollü bir kümeye aittir.

## 2. Kurulum ve çalıştırma
Ön koşullar:
- `backend/.env`: PostgreSQL bağlantısı. Değerler repoya eklenmez; örnek için `backend/.env.example`.
- Backend bağımlılıkları (`pip install -r backend/requirements.txt`) ve `pip install aiosmtpd`. SMTP yakalayıcı
  yalnızca şifre sıfırlama provası için gereklidir.
- Frontend bağımlılıkları (`cd frontend && npm ci`) ve Playwright Chromium.

Tam ön kontrol: H5-03 E2E regresyonu ile demo provası birlikte çalışır ve kanıtlar bu dizine yazılır.
```bash
bash e2e/h5-06/run.sh
```
Yalnızca demo provası:
```bash
DEMO_ONLY=1 bash e2e/h5-06/run.sh
```
Canlı demo için elle başlatma:
```bash
cd backend && python manage.py migrate && python manage.py runserver 127.0.0.1:8000
```
```bash
cd frontend && VITE_API_BASE_URL=http://127.0.0.1:8000 npx vite --port 5173
```
Deney anlık görüntüsü, H5-05 sonuçları değişirse yeniden üretilir; `--check` ile güncelliği doğrulanır:
```bash
python -m demo.h5_06.export_experiment_snapshot --check
```

## 3. Demo öncesi kontrol listesi
- [ ] `pg_isready`: PostgreSQL bağlantı kabul ediyor.
- [ ] `python manage.py check` temiz ve `migrate` güncel.
- [ ] Backend `http://127.0.0.1:8000/api/auth/me/` adresinde 401 döndürüyor; yani çalışıyor ve kimlik istiyor.
- [ ] Frontend `http://localhost:5173/login` açılıyor; `VITE_API_BASE_URL` doğru.
- [ ] Demo kullanıcıları oluşturuldu: `e2e/h5-03/create_test_users.py`.
  - Parolalar her çalıştırmada rastgele üretilir ve yalnızca geçici dosyada (izin 0600) tutulur.
  - Gerçek parola kullanılmaz.
- [ ] Örnek veriler hazır:
  - `e2e/h5-03/make_fixtures.py` → `ornek_api.zip`. Statik doğrulamadan geçer, hiçbir aşamada çalıştırılmaz.
  - `demo/h5_06/demo_data/referans_bes_metot.json` (5 metot).
- [ ] Şifre sıfırlama gösterilecekse yerel SMTP yakalayıcı çalışıyor (127.0.0.1:1025). Dışarı e-posta gönderilmez.
- [ ] `python -m demo.h5_06.export_experiment_snapshot --check` sonucu "güncel".
- [ ] API anahtarı gerekmez: demo hiçbir LLM çağrısı yapmaz; deney sonuçları çevrimdışıdır.

## 4. Alternatif gösterim planı
| Sorun | Belirti | Alternatif |
|---|---|---|
| PostgreSQL erişilemiyor | Backend başlamaz | Bu dizindeki ekran görüntüleri ve `demo-provasi-sonuclari.json` ile akış anlatılır; sorun canlı demoda gizlenmez |
| Backend durdu | Frontend "bağlantı hatası" gösterir (sahte başarı yok; H5-03 NET-1) | Backend yeniden başlatılır; oturum ve kayıtlar korunur (NET-2) |
| SMTP yakalayıcı yok | Sıfırlama e-postası gelmez | Şifre sıfırlama, H5-03 kanıtı `docs/mockup/h5-03/04-06` ile anlatılır |
| Frontend derlenmiyor | Vite hatası | `npm run build` çıktısı `vite preview` ile sunulur |
| Deney ekranı açılmıyor | — | `experiments/h5_05_hybrid_experiment/results/comparison_table.md` gösterilir |

## 5. Gerçek ve prototip (DEMO) özellik ayrımı
| Özellik | Durum | Not |
|---|---|---|
| Giriş, token yenileme, çıkış (SimpleJWT, refresh kara listesi) | **Gerçek** | H5-03 E2E: AUTH-1..3, E2E-17-18 |
| Hesap kilidi (3 hatalı giriş → 15 dk) ve kalan süre | **Gerçek** | Süre sunucudan gelir (LOCK-1..4) |
| Şifre sıfırlama (e-posta bağlantısı, token) | **Gerçek** | RESET-1..5 (yerel SMTP) |
| Korumalı sayfalar ve kullanıcı izolasyonu | **Gerçek** | E2E-19-22 |
| Proje yükleme, listeleme, detay, güncelleme, silme | **Gerçek** | PostgreSQL kalıcılığı; aktif analizde silme 409 |
| Referans gereksinim JSON (5 HTTP metodu) | **Gerçek** | Demo D-04; geçersiz metot (TRACE) reddedilir |
| AnalysisRun oluşturma, listeleme, detay | **Gerçek kayıt** | Kayıt QUEUED olarak kalır; analiz motoru bu sürümde bağlı değil |
| Deney sonuçları (`/experiments`) | **Çevrimdışı gerçek ölçüm** | H5-05 sonuç dosyasından kopyalanır (SHA-256 gösterilir); canlı analiz değildir |
| Kaynak kod analizi, üretilen testler, test sonuçları, bulgular, rapor ekranları | **Prototip / DEMO** | Yalnızca `/demo/analyses` altında örnek veriyle; gerçek analizde "henüz bağlı değil" |
| Test bazında ilerleme, tahmini kalan süre (canlı akış) | **Prototip / DEMO** | "Canlı · DEMO akışı (gerçek sandbox bağlantısı değil)" etiketi |
| Model/fallback bilgisi | **Prototip / DEMO** | Yalnızca DEMO üretilen testler ekranında |
| PDF rapor bölümü seçimi | **Prototip / DEMO** | PDF üretilmez; JSON örnek indirme DEMO etiketli |
| Raporlar menüsü | **Pasif** | Bağlantı değil (yer tutucu) |

## 6. Deney karşılaştırması (H5-05, çevrimdışı)
Kaynak: `experiments/h5_05_hybrid_experiment/results/comparison_table.md`. Model `groq/openai/gpt-oss-120b`,
istem `pytest_v1`, sıcaklık 0.0.

| Katman | Yöntem | Sözdizimi | İlk geçiş (pay/payda) | TP/FP/TN/FN | F1 | F1 ≥ 0,80 | Çalıştırılabilirlik ≥ %70 |
|---|---|---|---|---|---|---|---|
| A (20) | Kural tabanlı | 20/20 | 20/20 | 0/0/20/0 | Ölçülemedi | Ölçülemedi | Karşılandı |
| A (20) | Groq LLM | 20/20 | 20/20 | 0/0/20/0 | Ölçülemedi | Ölçülemedi | Karşılandı |
| A (20) | Hibrit | 20/20 | 20/20 | 0/0/20/0 | Ölçülemedi | Ölçülemedi | Karşılandı |
| B (17) | Kural tabanlı | 17/17 | 17/17 | 3/0/14/0 | 1,00 | Karşılandı | Karşılandı |
| B (17) | Groq LLM | 17/17 | 17/17 | 3/0/14/0 | 1,00 | Karşılandı | Karşılandı |
| B (17) | Hibrit | 17/17 | 17/17 | 3/0/14/0 | 1,00 | Karşılandı | Karşılandı |

Adlandırma kuralları:
- Precision, Recall ve F1 güvenlik tespitini (ground truth eşleşmesi) ölçer.
- Sözdizimi geçerliliği ve ilk geçişte çalıştırılabilirlik üretim kalitesini ölçer.
- Ölçülmemiş değerler veya hedefler gerçek sonuç gibi gösterilmez: "Ölçülemedi" çubuk olarak çizilmez.

## 7. Doğrulama sonuçları
| Kontrol | Sonuç | Kanıt |
|---|---|---|
| H5-03 gerçek E2E regresyonu: giriş, yenileme, çıkış, kilit, sıfırlama, CRUD, AnalysisRun, referans JSON, izolasyon, bağlantı kesintisi, 5 genişlik | **30/30 PASS**, konsol sorunu 0 | `e2e-regresyon-sonuclari.json` |
| Canlı demo provası (D-00..D-09, temizlik) | **11/11 PASS**, konsol sorunu 0 | `demo-provasi-sonuclari.json` |
| Navigasyon: giriş, şifre sıfırlama, dashboard, projeler, analiz alt ekranları, deney sonuçları | Çalışıyor | E2E + demo provası; ilgili birim testleri |
| Yatay taşma (390/768/1024/1440 px) | Yok | D-08 |
| Frontend birim testleri / typecheck / build | Bkz. PR açıklaması | `npx vitest run`, `npx tsc --noEmit`, `npm run build` |

## 8. Tespit edilen sorunlar ve durumları
| # | Sorun | Önem | Durum |
|---|---|---|---|
| 1 | Yeni "Deney sonuçları" ekranında 390 px (185 px) ve 768 px'te (3 px) yatay taşma: uzun kaynak yolu ve dar iki sütunlu kart | Demo kritik (mobil) | **Giderildi**: `break-all`, `min-w-0`, satır sarma, iki sütun `lg` ve üstünde. Demo provası yeniden 11/11 |
| 2 | Başlıkta yinelenen issue etiketi "(#43 (H5-05))" | Kozmetik | **Giderildi** |
| 3 | H5-04 testleri kendi dizininden çalıştırılınca `results/logs` altındaki üretilmiş modüller de toplanıyor (44 toplama hatası) | Düşük; demo dışı | Belgelendi. Doğru komut depo kökünden: `python -m pytest experiments/h5_04_generation_experiment/tests` (17 passed). H5-04 sorumlusuna bildirilmek üzere PR'da not edildi |
| 4 | Analiz motoru, test üretimi ve rapor servisleri backend'e bağlı değil | Bilinen kapsam | Ekranlar DEMO olarak ayrıldı; gerçek analizde "henüz bağlı değil" gösterilir (kapsam dışı geliştirme bu issue'ya taşınmadı) |

### Figma uyumu (docs/mockup/ekranlar ↔ demo ekran görüntüleri)
Bu oturumda ayrıntılı karşılaştırılan ekran: Genel bakış (02), uygulamanın ortak kabuğu (kenar menüsü, üst bar) ve
ortak bileşenler. Diğer ekranların Figma karşılaştırması canlı ortak provada bu tablo genişletilerek yapılmalıdır.
Bulgular kayda geçirildi; kapsam dışı geliştirmeler bu issue'ya taşınmadı.

| Ekran | Figma | Uygulama | Değerlendirme |
|---|---|---|---|
| Genel bakış | "Açık doğrulanmış bulgular" ve "Çalıştırılabilir test oranı" kartları; aktif analiz aşama şeridi; "Yeni analiz" düğmesi | Toplam/devam eden/tamamlanan analiz ve proje sayıları; aşama şeridi yalnızca aktif kayıt varsa | **Bilinçli fark:** bulgu ve oran servisleri backend'de yok; gerçek ekran bu değerleri uydurmaz. "Yeni analiz" kısayolu eksik (düşük önem; analiz proje detayından başlatılır) |
| Kenar menüsü | Alt kısımda kullanıcı kartı | Kullanıcı menüsü üst barda; "Deney sonuçları" öğesi eklendi | Düşük önem; tutarlı bileşenlerle çalışıyor |
| Üst bar | Sayfa adı (breadcrumb) | Tema anahtarı ve kullanıcı menüsü; sayfa başlığı içerikte | Düşük önem |
| Renk, yazı, kart, tablo ve rozet bileşenleri | Tasarım sistemi (00-Design System) | Ortak `Card`, `DataTable`, `Badge`, `MetricCard` | Uyumlu |

## 9. Kabul kriterleri izlenebilirliği
| AC | Durum | Kanıt |
|---|---|---|
| Ekranlar arası navigasyon ve temel tasarım tutarlılığı | Karşılandı | Demo D-01..D-09; ortak `Card`, `DataTable` ve `Badge` bileşenleri; taşma kontrolü |
| JWT giriş, hesap kilidi, şifre sıfırlama, korumalı sayfa | Karşılandı | Regresyon AUTH, LOCK, RESET ve E2E-17-22 |
| Proje yükleme ve CRUD gerçek API ile canlı gösterime hazır | Karşılandı | E2E-04..10, 23-25; demo D-02, D-03 |
| AnalysisRun ve referans gereksinim API'lerinin temel işlemleri | Karşılandı | E2E-11-16; demo D-04 (5 metot) ve D-05 |
| Gerçek ve mock/prototip bileşenler açıkça ayrılmış | Karşılandı | §5; DEMO rozetleri; "henüz bağlı değil" durumu; "ÇEVRİMDIŞI DENEY" etiketi |
| Üç yöntemin deney sonuçları ölçüm verisine uygun sunuluyor | Karşılandı | `/experiments`; anlık görüntü testi (`demo/h5_06/tests`) ve frontend testleri |
| Demo sırası, güvenli örnek veriler ve kurulum hazır | Karşılandı | §1–§3 |
| Kritik demo hataları giderilmiş veya belgelenmiş | Karşılandı | §8 |
| Yönergeler, ekran görüntüleri, karşılaştırma tablosu ve kanıtlar repoda | Karşılandı | Bu dizin |

**Not:** Merve ile birlikte yürütülmesi gereken ortak doğrulamalar (JWT akışları ve proje CRUD), gerçek
backend'e karşı otomatik E2E ile yapıldı. Canlı ortak prova için bu belgedeki kontrol listesi kullanılmalıdır.
