# Gerçek çalışan özellikler ↔ Prototip/DEMO bileşenler · H5-06 / #44

Demo sırasında neyin **gerçekten çalıştığını**, neyin **henüz prototip/DEMO** olduğunu açıkça ayırır.
Amaç: izleyiciye (hoca/jüri) olduğundan fazlasını göstermemek — akademik dürüstlük.

## ✅ Gerçek çalışan (canlı backend + PostgreSQL, bu demoda doğrulandı)

| Özellik | Kanıt |
|---|---|
| SimpleJWT giriş / access-refresh / korumalı sayfa | Smoke 1–2; `ProtectedRoute` + gerçek token akışı |
| Çıkış ve oturum yönetimi | Backend auth testleri; frontend oturum bağlamı |
| Hesap kilidi / kaba kuvvet koruması (django-axes + throttle) | Smoke 10 (401→429); backend axes testleri (3-hata→15dk) |
| Şifre sıfırlama (talep + yeni parola) | Smoke 9; konsol e-posta backend'i; frontend ekranları |
| Proje oluşturma (`multipart`) + **arşiv güvenlik doğrulaması** | Smoke 4; detayda doğrulama raporu (manage.py/DRF algısı, SHA-256) |
| Proje listeleme / detay / güncelleme (PATCH) / silme | Smoke 3,5,6,8 |
| Kullanıcı sahipliği / erişim kontrolü (başkasının kaydı → 404) | Smoke 7 |
| PostgreSQL veri kalıcılığı | Yüklenen proje kalıcı; detay SHA-256 ile doğrulanır |
| AnalysisRun **kaydı** oluşturma (QUEUED) + referans gereksinim JSON yükleme/görüntüleme | Proje detay ekranı; backend API |
| Referans JSON'da GET/POST/PUT/PATCH/DELETE doğrulaması | `referans-gereksinimler.json`; backend kısıtı/serializer |
| Dashboard gerçek sayıları (proje/analiz) | ss 04 (Toplam proje: 1) |
| Açık/koyu tema, ortak tasarım sistemi, navigasyon | 14 ekran görüntüsü |

## 🟡 Prototip / DEMO (henüz gerçek servise bağlı değil — açıkça işaretli)

| Bileşen | Durum | Nerede görünür |
|---|---|---|
| **Analiz yürütme motoru** (AST → LLM üretimi → Docker sandbox → güvenlik taraması → rapor) | Kayıt QUEUED oluşturulur ama **otomatik yürütülmez**; bu sürümde uçtan uca pipeline bağlı değil | Proje detay: "Bu sürümde analiz motoru otomatik başlatılmaz" |
| **Analiz sonuç ekranları** (kaynak kod analizi, üretilen testler, test sonuçları, güvenlik bulguları, rapor) | **DEMO veriyle** gösterilir (mock) | `/demo/analyses/...`; her ekranda "DEMO / Örnek veri: gerçek bir analiz değildir" rozeti (ss 09–14) |
| Test bazında ilerleme + tahmini kalan süre | Prototip gösterim (gerçek yürütmeye bağlı değil) | DEMO analiz ekranları |
| LLM model/fallback **canlı davranışı** | UI'da seçilebilir; canlı analiz motoru bağlı olmadığından uçtan uca tetiklenmez | Proje detay "Analiz başlat" formu |
| PDF rapor bölümü seçimi / indirme | Prototip (rapor üretimi demo) | DEMO rapor ekranı (ss 14) |

## Sınır neden burada?

Hafta 5 kapsamı **frontend + entegrasyon + ara demo**dur. Analiz motorunun backend'e uçtan uca
entegrasyonu **Hafta 6** issue'larıdır (ör. AI test üretimi servisinin backend'e entegrasyonu,
üretilen testlerin kaydı, güvenlik taraması). Bu nedenle analiz **sonuçları** demoda prototip/DEMO
veriyle gösterilir; altyapı (kayıt, referans gereksinim, sahiplik, kalıcılık) ise **gerçektir**.

Üretim yaklaşımlarının (kural tabanlı / LLM / hibrit) **gerçek** deneysel sonuçları ayrıca
[`karsilastirma-tablosu.md`](karsilastirma-tablosu.md)'nde sunulur (H5-04 ve H5-05 çıktıları).
