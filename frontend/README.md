# Frontend (Hafta 5 — #39 frontend temeli, #40 analiz ve sonuç ekranları)

React 18 + TypeScript + Vite + Tailwind CSS tabanlı arayüz temeli. Bu pakette giriş / şifre
sıfırlama / oturum sonu, genel bakış (dashboard), proje yönetimi (liste, detay, yükleme,
düzenleme, silme), profil ve durum ekranları (yetkisiz, bulunamadı) bulunur. #40 ile analiz
listesi ve analiz detayı (kaynak kod analizi, üretilen testler, test sonuçları, güvenlik
bulguları, rapor) eklenmiştir.

> **Mock veri uyarısı:** Bu arayüz henüz gerçek API'ye bağlı değildir. Ekranlarda görünen
> **tüm değerler (kullanıcı, projeler, analiz çalıştırmaları, sayılar, tarihler) örnektir**;
> gerçek bir analiz sonucunu veya metriği temsil etmez. Mock katmanı `src/lib/api/` altındadır
> (`auth.ts`, `projects.ts`, `analysis-runs.ts`, `mock/`). Gerçek HTTP/JWT entegrasyonu **#41**'dedir.

## Gereksinimler

- Node.js v24.13.0 (ekip sürümü) ve npm

## Kurulum

```bash
cd frontend
npm install
```

## Çalıştırma (geliştirme)

```bash
npm run dev
```

Vite geliştirme sunucusu başlar (varsayılan: <http://localhost:5173>). Mock girişte herhangi bir
kullanıcı adı/parola kabul edilir; yalnızca `yanlis-parola` parolası hatalı kimlik ve (3. denemede)
hesap kilidi senaryosunu tetikler. Şifre sıfırlama onayında `gecersiz-token` değeri geçersiz token
senaryosudur.

Başlıca rotalar: `/login`, `/forgot-password`, `/reset-password`, `/session-expired`,
`/dashboard`, `/projects`, `/projects/new`, `/projects/:id`, `/projects/:id/edit`, `/profile`,
`/forbidden`, `/analyses`, `/analyses/:id/{endpoints,tests,results,findings,report}`.

## Test

```bash
npm run test        # vitest run (jsdom + Testing Library)
npm run typecheck   # tsc --noEmit
```

## Üretim derlemesi

```bash
npm run build       # tsc --noEmit && vite build  -> dist/
npm run preview     # derlenmiş çıktıyı yerelde önizler
```

`dist/` git tarafından yok sayılır.

## Tema: J kimliği

Arayüz **J görsel kimliğini** kullanır (renkler `src/index.css` içinde CSS değişkenleri olarak
tanımlıdır; Tailwind bunları kullanır).

- **Açık tema varsayılandır.** Başlangıç teması sırasıyla `localStorage` (`theme` anahtarı) →
  `prefers-color-scheme` → açık tema şeklinde belirlenir; `localStorage` erişilemezse sessizce
  açık/sistem temasına düşer.
- Üst çubuktaki **koyu mod düğmesi** ile açık/koyu tema arasında geçiş yapılır; seçim
  `localStorage`'a yazılır.
- Kenar menüsündeki avatar baş harfleri `bg-accent` zemin + `text-accent-fg` metin ile çizilir.
  Kontrast oranları (WCAG, token değerlerinden hesaplanmıştır): açık tema `#ffffff` / `#0f6b7a`
  ≈ 6.17:1, koyu tema `#06211f` / `#3fd0d6` ≈ 9.00:1 (normal metin için 4.5:1 eşiğinin üzerinde).

## Ekran görüntüleri (manuel yakalama)

Bu pakette ekran görüntüleri **otomatik alınmamıştır**: otomatik tarayıcı aracı (Playwright /
Puppeteer vb.) ağır bağımlılık olduğu için bilerek eklenmemiştir. Görüntüler elle şu adımlarla
alınır ve `docs/mockup/j-kimligi/` altına konur:

1. `cd frontend && npm install && npm run dev` ile uygulamayı başlatın, tarayıcıda
   <http://localhost:5173> adresini açın.
2. **Açık tema:** Üst çubuktaki tema düğmesiyle açık temayı seçin (varsayılan). Aşağıdaki üç
   ekranı sırayla açıp tarayıcı geliştirici araçlarının "tam sayfa ekran görüntüsü" özelliğiyle
   (Chrome/Edge: DevTools → `Ctrl+Shift+P` → "Capture full size screenshot") yakalayın:
   - Giriş: `/login`
   - Genel bakış: `/dashboard` (herhangi bir bilgiyle giriş yaptıktan sonra)
   - Proje yükleme: `/projects/new`
3. **Koyu tema:** Koyu mod düğmesine basın ve aynı üç ekranı tekrar yakalayın.
4. Dosyaları `docs/mockup/j-kimligi/` klasörüne şu adlarla kaydedin:

   | Dosya | Ekran |
   | --- | --- |
   | `01-giris-acik.png`, `01-giris-koyu.png` | Giriş |
   | `02-genel-bakis-acik.png`, `02-genel-bakis-koyu.png` | Genel bakış |
   | `03-proje-yukleme-acik.png`, `03-proje-yukleme-koyu.png` | Proje yükleme |

5. Her iki temada kenar menüsündeki avatar baş harflerinin okunur olduğunu gözle doğrulayın.

Mevcut Figma tabanlı mockup görüntüleri `docs/mockup/ekranlar/` altındadır; J kimliği görüntüleri
bunlardan ayrı tutulur.

## Analiz ve sonuç ekranları (#40)

> **DEMO veri:** Analiz ekranlarındaki endpoint, test, sonuç, bulgu ve metrik değerlerinin tamamı
> `src/lib/api/mock/analysis-results.ts` içindeki **örnek** verilerdir; her ekranda "DEMO"
> etiketiyle belirtilir. Gerçek analiz, sandbox yürütmesi veya tarama sonucu değildir.

| Rota | Ekran | İçerik |
| --- | --- | --- |
| `/analyses` | Analiz listesi | Tüm analizler; `?project=<id>` ile projeye göre süzülür |
| `/analyses/:id/endpoints` | Kaynak kod analizi | GET/POST/PUT/PATCH/DELETE filtresi, arama, kimlik doğrulama / izin / kapsam filtreleri, filtre temizleme, boş sonuç durumu |
| `/analyses/:id/tests` | Pytest üretimi | Kural tabanlı / LLM ayrımı (analiz yöntemi: kural, LLM, hibrit), kod önizleme + kopyalama, doğrulama durumu, sağlayıcı / model / fallback bilgisi |
| `/analyses/:id/results` | Test sonuçları | PENDING, RUNNING, PASS, FAIL, ERROR, TIMEOUT (+ NOT_RUN/STOPPED) ayrı; canlı ilerleme (tamamlanan/toplam, yüzde, **tahmini** kalan süre), canlı çıktı, durum dağılımı grafiği |
| `/analyses/:id/findings` | Güvenlik bulguları | Doğrulama sınıfı (VERIFIED/POSSIBLE/UNCERTAIN) ile önem derecesi ayrı; kanıt, düzeltme önerisi, referans; önem dağılımı grafiği |
| `/analyses/:id/report` | Raporlama | Bölüm seçimi, PDF/JSON, hazırlanıyor / hazır / hata / veri yok durumları; değerlendirme metrikleri (Precision, Recall, F1) ve grafiği |

Önemli kurallar:

- **Analiz aşaması** (`AnalysisRun.status`: kuyruk → analiz → üretim → çalıştırma → tarama →
  tamamlandı) test durumlarından ayrı gösterilir.
- **Precision / Recall / F1** yalnızca altın etiketli referans (TP/FP/FN) varsa gösterilir;
  PASS/FAIL sayılarından türetilmez. Payda sıfırsa değer **"Ölçülemedi"** yazılır
  (`src/lib/evaluation-metrics.ts`, `agent/evaluation/metrics.py` ile aynı tanım).
- Kalan süre her zaman "tahmin" olarak yazılır; 3'ten az tamamlanmış test varsa "Belirsiz" denir.
- Canlı akış DEMO'dur (#2 numaralı analiz); zamanlayıcı sayfadan çıkınca temizlenir.
- Kod ve test çıktıları güvenilmeyen düz metin olarak çizilir (HTML yorumlanmaz).
- JSON indirme DEMO içeriktir; blob URL'si hemen serbest bırakılır. PDF dosyası frontend'de
  üretilmez, backend rapor servisine (#41 sonrası) bırakılmıştır.

**API hazırlığı:** Ekranlar yalnızca `src/lib/api/analysis-results.ts` fonksiyonlarını çağırır
(`listEndpoints`, `listGeneratedTests`, `listTestResults`, `listSecurityFindings`,
`getEvaluation`, `subscribeExecution`, `prepareReport`). Gerçek entegrasyonda (#41) yalnızca bu
fonksiyonların gövdeleri değişir; mock veri `mock/` klasöründe ayrı tutulur.

**Ekran görüntüleri:** Playwright ile 1440 px (mobil: 390 px) genişlikte alınmıştır;
`docs/mockup/h5-02/` altındadır. Tarayıcı kontrolü 1440 / 1280 / 1024 / 768 / 390 px'de yatay
taşma ve konsol hatası olmadan geçmiştir.

## Kapsam sınırları

Bu paket **#39 (frontend temeli)** ve **#40 (analiz, test üretimi ve sonuç ekranları)**
kapsamındadır. Kapsam dışı:

- **#41** — Gerçek HTTP/JWT ve analiz API entegrasyonu, token saklama, 401/refresh akışı,
  gerçek PDF indirme. Şu an tüm veri mock/DEMO.
- "Yeni analiz" sihirbazı, analiz ayarları ve referans gereksinim ekranları.
- Kenar menüsündeki "Raporlar" sayfası (rapor işlemleri analiz detayındaki "Rapor" sekmesindedir).
- Figma dosyasının J kimliğine güncellenmesi (hoca onayına bağlı, ayrı iş).
