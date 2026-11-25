# Frontend (Hafta 5, #39 — Frontend temeli)

React 18 + TypeScript + Vite + Tailwind CSS tabanlı arayüz temeli. Bu pakette giriş / şifre
sıfırlama / oturum sonu, genel bakış (dashboard), proje yönetimi (liste, detay, yükleme,
düzenleme, silme), profil ve durum ekranları (yetkisiz, bulunamadı) bulunur.

> **Mock veri uyarısı:** Bu arayüz henüz gerçek API'ye bağlı değildir. Ekranlarda görünen
> **tüm değerler (kullanıcı, projeler, analiz çalıştırmaları, sayılar, tarihler) örnektir**;
> gerçek bir analiz sonucunu veya metriği temsil etmez. Mock katmanı `src/lib/api/` altındadır
> (`auth.ts`, `projects.ts`, `analysis-runs.ts`, `mock/`). Gerçek HTTP/JWT entegrasyonu **#41**'dedir.

## Gereksinimler

- Node.js 18+ ve npm

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
`/forbidden`.

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

## Kapsam sınırları

Bu paket yalnızca **#39 (frontend temeli)** kapsamındadır. Kapsam dışı:

- **#41** — Gerçek HTTP/JWT entegrasyonu, token saklama, 401/refresh akışı. Şu an tüm veri mock.
- **#40** — Analiz ekranları: analiz ayarları, endpointler, üretilen testler, test sonuçları,
  güvenlik bulguları, rapor, "Yeni analiz" sihirbazı, referans gereksinimler.
- Recharts grafikleri (#40/#43).
- Figma dosyasının J kimliğine güncellenmesi (hoca onayına bağlı, ayrı iş).
