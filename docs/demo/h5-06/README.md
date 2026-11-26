# H5-06 — Canlı Demo ve Frontend Entegrasyon Kontrolü · Issue #44

Hafta 5 frontend'inin gerçek backend API'leriyle uçtan uca çalıştığını doğrulayan ve ara demoya
hazır, tekrarlanabilir bir gösterim paketidir. Çalışan özellikler ile henüz prototip/DEMO aşamasındaki
bileşenler **açıkça ayrılmıştır** (bkz. [`gercek-vs-prototip.md`](gercek-vs-prototip.md)).

> **Bu paket neyi kanıtlar?** Canlı yığın (PostgreSQL + Django/DRF + React/Vite) ayağa kaldırılarak
> gerçek HTTP istekleriyle giriş/JWT, hesap kilidi koruması, şifre sıfırlama, proje CRUD + arşiv
> doğrulama, sahiplik ve referans gereksinim akışları doğrulanmıştır. Kanıt ve sayılar:
> [`dogrulama.md`](dogrulama.md). Ekran görüntüleri (koyu tema):
> [`ekran-goruntuleri/`](ekran-goruntuleri/). Üç yöntem karşılaştırması:
> [`karsilastirma-tablosu.md`](karsilastirma-tablosu.md).

## 1. Demo sırası (önerilen akış)

Giriş → Dashboard → Proje yükleme → Proje listeleme/detay → (Analiz kaydı + Referans JSON) →
Deney sonuçları (karşılaştırma) → DEMO analiz ekranları.

| # | Adım | Ekran / kanıt | Not |
|---|---|---|---|
| 1 | Giriş (JWT) | `ekran-goruntuleri/01-giris.png`, `04-dashboard.png` | `demo_merve` ile giriş; dashboard gerçek sayıları gösterir |
| 2 | Şifremi unuttum / yeni parola | `02-sifremi-unuttum.png`, `03-yeni-parola-belirleme.png` | Konsol e-posta backend'i (SMTP gerekmez) |
| 3 | Proje yükleme | `07-proje-yukleme.png` + `demo-verileri/ornek-proje.zip` | `multipart/form-data`; arşiv güvenlik doğrulaması |
| 4 | Proje listeleme / detay | `05-projeler-liste.png`, `06-proje-detay.png` | Detayda arşiv SHA-256 + doğrulama raporu (manage.py/DRF algısı) |
| 5 | Analiz kaydı + Referans JSON | `06-proje-detay.png` (alt bölümler) + `demo-verileri/referans-gereksinimler.json` | AnalysisRun QUEUED oluşturulur; referans JSON GET/POST/PUT/PATCH/DELETE kapsar |
| 6 | Deney sonuçları | [`karsilastirma-tablosu.md`](karsilastirma-tablosu.md) | Kural tabanlı / LLM / hibrit; H5-04 + H5-05 gerçek çıktıları |
| 7 | DEMO analiz ekranları | `09-...` → `14-...` | Analiz/test/sonuç/bulgu/rapor ekranları **DEMO veriyle** (prototip, açıkça rozetli) |

## 2. Kurulum ve çalıştırma

Ön koşullar: Docker (PostgreSQL için), Python 3.11 (backend sanal ortamı), Node.js + npm (frontend).

```bash
# 1) PostgreSQL (port 5433) — Docker
docker start h4pg 2>/dev/null || docker run -d --name h4pg \
  -e POSTGRES_DB=ai_test_agent -e POSTGRES_USER=ai_test_agent -e POSTGRES_PASSWORD=<demo-parola> \
  -p 5433:5432 postgres:16
# (demo için backend/.env'deki POSTGRES_* ile aynı olmalı; gerçek parola repoya yazılmaz)

# 2) Backend
cd backend
# .env zaten yerel demo değerleriyle hazır (gitignore'lu). Gerekirse: cp .env.example .env
bvenv/Scripts/python.exe manage.py check_database
bvenv/Scripts/python.exe manage.py migrate
# Demo kullanıcılarını tohumla (bkz. demo-verileri/demo-kullanicilar.md)
bvenv/Scripts/python.exe manage.py runserver 127.0.0.1:8000

# 3) Frontend (ayrı terminal)
cd frontend
npm install            # recharts dahil bağımlılıkları kurar (H5-05 sonrası gerekli)
npm run dev            # http://localhost:5173  (API tabanı varsayılan http://localhost:8000)
```

Tarayıcıda `http://localhost:5173` → `demo_merve` / `DemoParola!2026` ile giriş.

## 3. Demo verileri

[`demo-verileri/`](demo-verileri/) altında (hiçbiri gerçek sır/parola değildir):

- `demo-kullanicilar.md` — 3 demo kullanıcı + tohumlama komutu (kilit demosu için ayrı kullanıcı).
- `ornek-proje.zip` + `ornek-proje/` — güvenli örnek Django/DRF projesi (yükleme demosu için).
- `referans-gereksinimler.json` — 5 HTTP metodunu (GET/POST/PUT/PATCH/DELETE) kapsayan ACCESS_RULE
  referans gereksinimleri.

## 4. Demo öncesi kontrol listesi

- [ ] Docker çalışıyor, `h4pg` konteyneri ayakta (`docker ps`), port 5433 erişilebilir.
- [ ] `manage.py check_database` başarılı (PostgreSQL bağlantısı).
- [ ] Backend `http://127.0.0.1:8000` ayakta; `POST /api/auth/login/` 200 döner.
- [ ] Demo kullanıcıları tohumlandı.
- [ ] Frontend `npm install` yapıldı (recharts), `npm run dev` ayakta (5173).
- [ ] CORS: backend `CORS_ALLOWED_ORIGINS` içinde `http://localhost:5173` var (varsayılan).
- [ ] `demo_kilit` kullanıcısı kilitli değil (`manage.py axes_reset`).

## 5. Alternatif gösterim planı (bağlantı/servis sorunu olursa)

- **Backend/PostgreSQL ayağa kalkmazsa:** canlı tıklama yerine bu paketteki **ekran görüntüleri**
  (gerçek backend'e bağlı, koyu tema) ve [`dogrulama.md`](dogrulama.md) kanıtları (470 backend + 255
  frontend testi, canlı smoke 10/10) gösterilir.
- **Frontend derlenmezse:** `npm install` çalıştırılır (recharts eksikse); `npm run build` kanıtı
  `dogrulama.md`'de.
- **DEMO analiz ekranları** canlı AI gerektirmez (mock veri); internet/Groq olmadan gösterilebilir.

## 6. Paket içeriği

| Dosya | İçerik |
|---|---|
| [`dogrulama.md`](dogrulama.md) | Kabul kriterleri eşlemesi + gerçek test/smoke kanıtları |
| [`gercek-vs-prototip.md`](gercek-vs-prototip.md) | Çalışan özellikler ↔ prototip/DEMO bileşenler |
| [`karsilastirma-tablosu.md`](karsilastirma-tablosu.md) | Kural tabanlı / LLM / hibrit üretim karşılaştırması |
| [`bilinen-sinirliliklar.md`](bilinen-sinirliliklar.md) | Tespit edilen sınırlılıklar ve sahipleri |
| [`ekran-goruntuleri/`](ekran-goruntuleri/) | 14 koyu tema ekran görüntüsü (canlı backend) |
| [`demo-verileri/`](demo-verileri/) | Demo kullanıcıları, örnek proje arşivi, referans JSON |
| [`scripts/live_smoke.py`](scripts/live_smoke.py) | Canlı API smoke testi (tekrarlanabilir kanıt) |
