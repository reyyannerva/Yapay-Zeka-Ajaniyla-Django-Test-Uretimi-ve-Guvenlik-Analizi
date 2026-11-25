# Frontend (Hafta 5 — #39 frontend temeli, #40 analiz ve sonuç ekranları, #41 gerçek API entegrasyonu)

React 18 + TypeScript + Vite + Tailwind CSS tabanlı arayüz temeli. Bu pakette giriş / şifre
sıfırlama / oturum sonu, genel bakış (dashboard), proje yönetimi (liste, detay, yükleme,
düzenleme, silme), profil ve durum ekranları (yetkisiz, bulunamadı) bulunur. #40 ile analiz
listesi ve analiz detayı (kaynak kod analizi, üretilen testler, test sonuçları, güvenlik
bulguları, rapor) eklenmiştir.

> **Gerçek API (H5-03 / #41):** Giriş, token yenileme, çıkış, hesap kilidi, şifre sıfırlama, proje
> CRUD (multipart yükleme dahil), analiz kaydı (oluşturma/listeleme/detay) ve referans gereksinim
> JSON işlemleri gerçek Django/DRF API'sine bağlıdır; veriler PostgreSQL'de saklanır. Ortak istemci
> `src/lib/api/client.ts`, oturum `src/lib/auth-context.tsx` ve `src/lib/api/token-store.ts`.
> Analiz **sonuç** ekranları (endpoint, Pytest, test yürütme, bulgu, rapor) için backend servisi henüz
> yoktur; bunlar yalnızca `/demo/analyses` altında açıkça **DEMO** etiketli prototip olarak durur ve
> gerçek kayıtlarla karıştırılmaz. Kurulum ve ayrıntı: [`docs/integration/h5-03/README.md`](../docs/integration/h5-03/README.md).

## Gereksinimler

- Node.js v24.13.0 (ekip sürümü) ve npm

## Kurulum

```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_BASE_URL: Django API adresi (gizli değer içermez)
```

## Çalıştırma (geliştirme)

```bash
npm run dev
```

Vite geliştirme sunucusu başlar (varsayılan: <http://localhost:5173>). Arayüz çalışan bir Django
backend'i (`VITE_API_BASE_URL`, varsayılan `http://localhost:8000`) ve gerçek kullanıcı hesabı
gerektirir; backend'e ulaşılamazsa kullanıcıya bağlantı hatası gösterilir (örnek veriye geçilmez).

Başlıca rotalar: `/login`, `/forgot-password`, `/reset-password`, `/session-expired`,
`/dashboard`, `/projects`, `/projects/new`, `/projects/:id`, `/projects/:id/edit`, `/profile`,
`/forbidden`, `/analyses`, `/analyses/:id/summary` (gerçek kayıt), `/demo/analyses`,
`/demo/analyses/:id/{endpoints,tests,results,findings,report}` (DEMO prototip).

## Test

```bash
npm run test        # vitest run (jsdom + Testing Library)
npm run typecheck   # tsc --noEmit
```

Birim/bileşen testleri gerçek istemci ve servis kodunu çalıştırır; yalnızca `fetch`, Django/DRF
sözleşmesini taklit eden bellek içi sahte backend'e (`src/test/fake-api.ts`) yönlendirilir. Bu testler
gerçek backend/PostgreSQL kanıtı değildir; gerçek uçtan uca testler `e2e/h5-03/` altındadır.

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

> **DEMO veri:** Aşağıdaki sonuç ekranlarının endpoint, test, sonuç, bulgu ve metrik değerlerinin
> tamamı `src/lib/api/mock/analysis-results.ts` içindeki **örnek** verilerdir ve yalnızca
> `/demo/analyses` altında, "DEMO" etiketiyle gösterilir (#41 ile gerçek kayıtlardan ayrıldı).
> Gerçek bir analiz kaydı (`/analyses/:id`) bu sekmelerde "henüz bağlı değil" durumunu gösterir.

| Rota | Ekran | İçerik |
| --- | --- | --- |
| `/demo/analyses` | DEMO analiz listesi | Örnek analizler; `?project=<id>` ile süzülür |
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

(Tablodaki `/analyses/:id/...` sekmeleri DEMO kaynağında `/demo/analyses/:id/...` adresindedir.)

**API hazırlığı:** Sonuç ekranları yalnızca `src/lib/api/analysis-results.ts` fonksiyonlarını çağırır
(`listEndpoints`, `listGeneratedTests`, `listTestResults`, `listSecurityFindings`,
`getEvaluation`, `subscribeExecution`, `prepareReport`). İlgili backend uç noktaları eklendiğinde
yalnızca bu fonksiyonların gövdeleri değişir.

**Ekran görüntüleri:** Playwright ile 1440 px (mobil: 390 px) genişlikte alınmıştır;
`docs/mockup/h5-02/` altındadır. Tarayıcı kontrolü 1440 / 1280 / 1024 / 768 / 390 px'de yatay
taşma ve konsol hatası olmadan geçmiştir.

## Kapsam sınırları

Bu paket **#39**, **#40** ve **#41 (gerçek API entegrasyonu)** kapsamındadır. Kapsam dışı:

- Analiz sonuçları (endpoint, Pytest, yürütme, bulgu, metrik) ve gerçek PDF/JSON rapor uç noktaları:
  backend'de henüz yok; ekranlar DEMO prototip olarak kalır.
- Oturum içi parola değiştirme: backend uç noktası yok; profil ekranı e-posta ile sıfırlamaya yönlendirir.
- Kenar menüsündeki "Raporlar" sayfası (rapor işlemleri analiz detayındaki "Rapor" sekmesindedir).
- Figma dosyasının J kimliğine güncellenmesi (hoca onayına bağlı, ayrı iş).
