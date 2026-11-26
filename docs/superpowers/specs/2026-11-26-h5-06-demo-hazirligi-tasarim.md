# H5-06 (#44) — Frontend Entegrasyon Kontrolü ve Canlı Demo Hazırlığı — Tasarım Dokümanı

**Tarih:** 2026-11-26
**Issue:** #44 — H5-06 | Frontend Entegrasyon Kontrolü ve Canlı Demo Hazırlığı
**Sahip:** Merve Çaloğlu (mervecaloglu)
**Durum:** Tamamlandı (bu PR)

## 1. Amaç ve gerekçe

Hafta 5 frontend ekranlarının gerçek backend API'leriyle uçtan uca çalıştığını doğrulamak ve ara
demoya hazır, tekrarlanabilir bir gösterim paketi üretmek. Çalışan özellikler ile prototip/DEMO
bileşenler açıkça ayrılır (akademik dürüstlük).

## 2. Kullanıcı kararları (2026-11-26)

- **Doğrulama yolu:** Tam canlı yığın (Docker PostgreSQL + Django/DRF + React/Vite) ayağa kaldırılır;
  yeni ekran görüntüleri otomatik alınır (kullanıcı onayı).
- **Kusur politikası:** Başkasının (Reyyan #40/#41/#43) veya backend kodunda demo-engelleyici kusur
  bulunursa **sadece belgelenir; koda dokunulmaz** (CLAUDE.md ekip sınırı).
- **Ekran görüntüleri:** Otomatik (Playwright), tercihen **koyu tema**. Playwright frontend/package.json'a
  dokunmadan ayrı kurulur.

## 3. Yaklaşım

1. Canlı yığını ayağa kaldır: `h4pg` PostgreSQL (5433), backend (`runserver` 8000), frontend (`vite` 5173).
2. **Gerçek kanıt üret:** backend test suite, frontend test + build, canlı API smoke testi (stdlib,
   token/parola redakte).
3. **Ekran görüntüleri:** Playwright ile koyu tema, canlı backend'e bağlı 14 ekran.
4. **Demo verisi:** 3 demo kullanıcı (demo parola), güvenli örnek Django/DRF proje arşivi, 5 metotlu
   referans gereksinim JSON.
5. **Demo paketi dokümanları:** demo sırası/kurulum/fallback, gerçek-vs-prototip, 3 yöntem
   karşılaştırması (H5-04 + H5-05 gerçek verisi), kabul kriteri eşlemesi, bilinen sınırlılıklar.

## 4. Hedef olmayanlar / sınırlar

- Analiz yürütme motorunu (AST→LLM→sandbox→tarama→rapor) canlıya bağlamak — **Hafta 6** kapsamı; demoda
  analiz sonuç ekranları DEMO veriyle gösterilir.
- Reyyan'ın frontend/backend koduna müdahale (yalnızca `npm install` gibi ortam kurulumu yapılır).
- Metrik/sonuç uydurmak; ölçülmemiş metriği gerçek gibi sunmak.

## 5. Teslim

`docs/demo/h5-06/` paketi: README (demo sırası/kurulum/fallback), dogrulama.md (kabul kriteri + kanıt),
gercek-vs-prototip.md, karsilastirma-tablosu.md, bilinen-sinirliliklar.md, ekran-goruntuleri/ (14 PNG +
index), demo-verileri/ (kullanıcılar, örnek proje + zip, referans JSON), scripts/ (live_smoke.py,
screenshot.js), evidence/ (live_smoke_result.json).

## 6. Doğrulama durumu (gerçek, çalıştırıldı)

- Backend: 470 passed, 1 skipped (PostgreSQL 16).
- Frontend: 255 passed (37 dosya) + `npm run build` başarılı.
- Canlı API smoke: 10/10 adım geçti.
- 14 ekran görüntüsü (koyu tema, canlı backend).
