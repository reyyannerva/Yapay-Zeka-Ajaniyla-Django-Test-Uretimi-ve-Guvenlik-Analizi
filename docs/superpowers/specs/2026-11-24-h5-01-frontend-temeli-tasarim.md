# H5-01 (#39) — Frontend Temeli ve Proje Yönetimi Arayüzü — Tasarım Dokümanı

**Tarih:** 2026-11-24
**Issue:** #39 — H5-01 | Proje Yönetimi ve Yükleme Frontend'inin Geliştirilmesi
**Sahip:** Merve Çaloğlu (mervecaloglu)
**Durum:** Taslak — onay bekliyor (henüz commit edilmedi; onaydan sonra `feat/h5-01-frontend-temeli` branch'inde)
**Görsel kimlik kararı (2026-11-25):** **J "Gece-Sinyal"** — açık tema varsayılan + koyu mod (Merve + Reyyan onayı; bkz. §6.5, §8.7).

---

## 1. Amaç ve gerekçe (niçin)

Proje şu ana kadar backend-only ilerledi (Django/DRF, PostgreSQL, hazır API'ler). Hafta 5'te
frontend'e başlıyoruz. Frontend iki issue'ya bölünmüş durumda:

- **#39 (Merve, bu doküman):** kimlik doğrulama + dashboard + proje yönetimi/yükleme.
- **#40 (Reyyan):** analiz ayarları + endpointler + üretilen testler + sonuçlar + bulgular + rapor.

İkisi **tek bir uygulama**. Bu nedenle #39, yalnızca kendi ekranlarını değil, her iki issue'nun
paylaşacağı **ortak temeli** de kurar: tasarım sistemi (Tailwind teması), yönlendirme, uygulama
kabuğu (sidebar/üstbar), API istemci katmanı + TanStack Query kurulumu ve **ortak TypeScript
tipleri**. Reyyan #40'ı bu temelin üzerine inşa eder. Bu karar kullanıcı (Merve) ve Reyyan
tarafından onaylandı.

Bu aşamada ekranlar **mock veri** ile çalışır. Gerçek API entegrasyonu **#41 (H5-03)** kapsamıdır;
temel, #41'de bileşenler değişmeden gerçek HTTP'ye geçilebilecek şekilde tasarlanır.

## 2. Hedefler

1. `frontend/` altında çalışan React + Vite + TypeScript + Tailwind CSS projesi.
2. **J "Gece-Sinyal" görsel kimliği** (açık tema varsayılan + koyu mod) ile token-merkezli **Tailwind
   teması** ve yeniden kullanılabilir ortak bileşenler. Ekran yapısı Figma'yla aynı; değişen yalnızca
   kimlik (renk + font + imza detaylar + koyu mod). Açık/koyu geçişi `ThemeToggle` ile, tercih
   `localStorage`'da. Token değerleri §8.7.
3. Yönlendirme + korumalı rotalar + tek `<AppLayout>` kabuğu (sidebar, üstbar, kullanıcı menüsü).
4. **Kimlik doğrulama akışı** (mock): giriş, giriş hatası + hesap kilidi gösterimi, oturum süresi
   doldu, şifremi unuttum ve yeni şifre belirleme.
5. **Dashboard / Genel bakış** (ekran 02): metrik kartları, devam eden analiz aşama şeridi, son
   analizler tablosu.
6. **Proje yönetimi:** proje listesi (19), proje detayı, proje oluşturma/yükleme (yeniden
   kullanılabilir bileşen), güncelleme, silme onayı (30).
7. **Durum ekranları:** ilk kullanım/boş durum (14), yetkisiz erişim (13), oturum süresi doldu (12),
   giriş hatası (11).
8. API sözleşmeleriyle birebir **ortak TypeScript tipleri** (`src/types`).
9. Gerçek endpoint imzalarına sahip, #41'de gerçek HTTP'ye çevrilebilen **mock servis katmanı**.
10. **TanStack Query** sağlayıcısı ve query-key konvansiyonu.
11. Mobil + masaüstü uyumluluk, temel erişilebilirlik.
12. **Gerçek testler** (Vitest + React Testing Library) ile doğrulama.
13. Ekran görüntüleri ve yerel çalıştırma yönergelerinin repoya eklenmesi.

## 3. Hedef olmayanlar (non-goals)

- Gerçek API bağlantısı — **#41**.
- Analiz ayarları, endpointler, üretilen testler, test sonuçları, güvenlik bulguları, rapor
  ekranları — **#40**.
- "Yeni analiz" sihirbazının kendisi — **#40** (bkz. §7 sınır sözleşmesi). #39 yalnızca sihirbazın
  kullanacağı yeniden kullanılabilir yükleme bileşenini verir.
- Referans gereksinimler ekranları (04, 23, 31) — **#40**.
- Celery canlı ilerleme polling'i (backend'de iş akışı henüz yok; analiz oluşturma QUEUED kaydı
  üretir) — sonraki haftalar.
- Recharts ile sonuç grafikleri — #40/#43.
- Kayıt (register) ekranı — tasarım gereği yok; hesaplar yönetici tarafından açılır.

## 4. Başarısızlık ölçütleri (anti-goals)

- Her iki geliştiricinin **ayrı tasarım sistemi / yinelenen tip** kurması → tutarsızlık ve çakışma.
- Mock verinin bileşen içine gömülmesi → #41'de bileşenlerin yeniden yazılması gerekmesi.
- Giriş formunun `username` tabanlı gerçek API'ye uyarlanamayacak biçimde sabit e-postaya bağlanması.
- Gerçekmiş gibi görünen **uydurma metrik/sonuç** gösterilmesi (tüm mock değerler açıkça örnektir).

## 5. Kısıtlar

- **Proje kuralları (CLAUDE.md):** her issue kendi feature branch'inde (`feat/h5-01-frontend-temeli`),
  Türkçe conventional-commit, **commit/PR'da AI imzası YOK**, her git işleminden önce onay,
  Reyyan'ın kod/issue'larına dokunulmaz, yalnızca aktif issue dosyaları değişir.
- **Yığın sabit** (docs/architecture/technology_stack.md): React, Vite, TypeScript, Tailwind CSS,
  TanStack Query, Recharts. **Araç listesi J kimliğiyle değişmez;** technology_stack.md font adı
  içermez, güncellenmeye gerek yok. Fontlar yeni bağımlılık değil, Google Fonts bağlantısıyla gelir.
- **Görsel kimlik: "J" (Gece-Sinyal) — KARAR.** Açık tema varsayılan, koyu mod düğmeyle. Fontlar:
  Space Grotesk (başlık) + Inter (gövde) + JetBrains Mono (kod/endpoint/test). Vurgu: açık `#0f6b7a`
  / koyu `#3fd0d6` (proje teali ailesi). Durum renkleri: PASS yeşil, FAIL **amber (uyarı)**, teknik
  hata kırmızı, süreç teal. Token değerleri §8.7. (Önceki Figma: IBM Plex + mavi süreç + turuncu
  FAIL; kimlik, hocanın "şablon gibi" geri bildirimi üzerine bilinçli olarak J'ye evrildi.)
- **Tasarım kaynağı:** Figma prototipi + `docs/mockup/ekranlar/*.png` (31 ekran) **yapısal referans**
  (düzen/akış); görsel kimlik J'ye göre uygulanır (§8.7).
- **Figma güncellemesi beklemede:** 31 ekranın Figma'da J'ye boyanıp boyanmayacağı **hoca onayına**
  bağlı; kod her durumda J. `docs/mockup/README.md:12` ve Figma dosyası karar gelince güncellenir —
  bu issue'nun işi değil.
- **Kanonik durumlar:** `AnalysisRun` 9 durumu (`QUEUED, ANALYZING, GENERATING, VALIDATING,
  EXECUTING, SCANNING, COMPLETED, FAILED, CANCELLED`) — arayüz bunlarla tutarlı olmalı.
- **API sözleşmeleri sabit** (docs/api/*): giriş `username` tabanlı, proje oluşturma
  `multipart/form-data`, proje/analiz sahiplik kontrolleri sunucuda.
- **Araç zinciri:** Node v24.13.0, **npm** (pnpm/yarn yok). Backend Python ortamından bağımsız.

## 6. Değerlendirilen yaklaşımlar

### 6.1 Ortak temelin sahipliği
- **(A) #39 ortak temeli kurar, #40 üzerine inşa eder — SEÇİLDİ.** #39 ilk sırada ve zaten
  auth + layout + routing içeriyor; temeli burada kurmak tek kaynak sağlar, çakışmayı en aza indirir.
- (B) Temeli birlikte ayrı bir ön-adımda kurmak. Daha fazla eşgüdüm; reddedildi.
- (C) Her geliştirici kendi temelini kurar. Tutarsızlık ve çakışma; reddedildi (anti-goal).

### 6.2 UI bileşen yaklaşımı
- **(A) Elle yazılmış Tailwind bileşenleri — SEÇİLDİ.** Bağımsızlık, tasarım sistemine birebir uyum,
  akademik prototip için şeffaflık. Erişilebilirlik gerektiren yerlerde (dialog, menü) küçük Radix
  primitive'leri seçmeli eklenebilir.
- (B) shadcn/ui (Radix). Daha hızlı başlangıç ama daha fazla bağımlılık + uyarlama; reddedildi.
- (C) MUI/AntD. Ağır, kendi tasarım dili; reddedildi.

### 6.3 Mock veri stratejisi
- **(A) Gerçek endpoint imzalı sahte servis katmanı — SEÇİLDİ.** `src/lib/api` içindeki fonksiyonlar
  gerçek imzalarla statik fixture döndürür; #41'de yalnızca gövde gerçek HTTP'ye çevrilir.
- (B) MSW ile HTTP taklidi. Daha gerçekçi ama bu aşamada fazladan katman; #41'de opsiyonel.
- (C) Veriyi bileşene gömmek. Reddedildi (anti-goal).

### 6.4 Mimari
- **Özellik-temelli klasörleme — SEÇİLDİ** (`src/features/*`), katman-temelli yerine; ekip bölünmesine
  ve #40'ın bağımsız eklenmesine uygun.

### 6.5 Görsel kimlik
Hoca mevcut Figma'yı "hazır şablon gibi, fazla klasik" bulup özelleştirme istedi. Tarayıcıda atılabilir
bir spike ile kimlik yönleri denendi (A–J). Değerlendirme iki **bağımsız eksende** yapıldı: *yerleşim*
(Figma yapısı korunur) ve *kimlik* (renk/font/karakter). Özgünlük çoğunlukla kimlik ekseninde olduğu
için yerleşim Figma'da bırakıldı, yalnızca kimlik değiştirildi.
- **(J) "Gece-Sinyal" — açık varsayılan + koyu mod — SEÇİLDİ.** Proje tealini korur (Figma'dan az
  sapma, hocaya savunması kolay); amber yalnızca uyarı/FAIL'de (temiz durum semantiği: FAIL ≠ sistem
  hatası); koyu mod Reyyan'ın tercihini karşılar, açık varsayılan metin-yoğun ekranlarda okunur kalır.
  Karar Merve + Reyyan ortak.
- (B) "Sinyal" (amber birincil): teali bırakıyor, uyarı rengini birincil yapıp semantiği bulandırıyor;
  reddedildi. (G/H açık, I koyu) J'nin bileşenleriydi, tek kimlikte birleştirildi.
- Sonuç: yalnızca renk/font değil **koyu mod** da eklenir; **ekran yerleşimi/akışı değişmez.**

## 7. #39 ↔ #40 inşa sınırı (ortak sözleşme)

- #39 şunları **verir**: `ProjectUpload` (yeniden kullanılabilir yükleme bileşeni), bağımsız proje
  CRUD/liste/detay, ortak tipler, ortak UI bileşenleri, `<AppLayout>`, auth + korumalı rotalar,
  TanStack Query kurulumu.
- #40 şunları **yapar**: "Yeni analiz" 3 adımlı sihirbazı (adım 1'de #39'un `ProjectUpload`
  bileşenini kullanır), analiz/sonuç/rapor ekranları.
- Reyyan'ın uyması gereken sözleşme: tipleri `src/types`'tan import eder; ortak bileşenleri
  `src/components/ui`'den kullanır; rotalarını paylaşılan `<AppLayout>` altına ekler; query-key
  konvansiyonunu izler.

> **Not (tasarım-sorumluluğu vs geliştirme-sorumluluğu):** Figma'daki H2 ekran çizim dağılımı ile
> H5 geliştirme dağılımı birebir örtüşmez (örn. "08 Test sonuçları"nı Merve çizmiş ama geliştirmesi
> #40). Geliştirmede **H5 issue kapsamı** esastır; mevcut PNG'ler, kim çizmiş olursa olsun ortak
> referanstır.

## 8. Kararlaştırılan tasarım (nasıl)

### 8.1 Klasör yapısı
```
frontend/
├─ index.html
├─ package.json            # npm
├─ vite.config.ts
├─ tsconfig.json
├─ tailwind.config.ts      # tasarım sistemi token'ları
├─ postcss.config.js
├─ .env.example            # VITE_API_BASE_URL (şimdilik kullanılmıyor, #41'de aktif)
└─ src/
   ├─ main.tsx             # React + Router + QueryClientProvider kökü
   ├─ App.tsx              # rota tanımları
   ├─ index.css            # Tailwind katmanları + Space Grotesk/Inter/JetBrains Mono (Google Fonts) + tema token'ları
   ├─ types/               # ORTAK: user, project, analysis-run, reference-requirement, api-error
   ├─ lib/
   │  ├─ api/              # ORTAK: gerçek imzalı servis fonksiyonları (şimdilik mock)
   │  │  ├─ client.ts      # fetch sarmalayıcı (base URL, auth header yeri) — #41'de dolar
   │  │  ├─ auth.ts, projects.ts, analysis-runs.ts
   │  │  └─ mock/          # statik fixture'lar (açıkça örnek veri)
   │  ├─ queryKeys.ts      # ORTAK: query-key konvansiyonu
   │  ├─ auth-context.tsx  # mock token/oturum durumu
   │  └─ theme-context.tsx # ORTAK: açık/koyu tema; kökte data-theme, tercih localStorage
   ├─ components/
   │  ├─ ui/               # ORTAK: Button, Input, Badge(StatusBadge), Card, MetricCard, DataTable,
   │  │                    #        StageStrip, EmptyState, Spinner, Toast, ConfirmDialog, Modal, ThemeToggle
   │  └─ layout/           # ORTAK: AppLayout, Sidebar, Topbar, UserMenu, ProtectedRoute
   └─ features/
      ├─ auth/             # Login, LoginError/kilit, SessionExpired, ForgotPassword, ResetPassword
      ├─ dashboard/        # Overview (02)
      └─ projects/         # ProjectList (19), ProjectDetail, ProjectUpload, ProjectEdit, DeleteConfirm (30)
```

### 8.2 Rotalar
| Yol | Ekran | Koruma |
|---|---|---|
| `/login` | 01 Giriş (+ 11 hata/kilit inline) | public |
| `/forgot-password` | 26 Şifre sıfırlama talebi | public |
| `/reset-password` | Yeni şifre belirleme (uid/token query) | public |
| `/` → `/dashboard` | 02 Genel bakış | korumalı |
| `/projects` | 19 Projeler (14 boş durum) | korumalı |
| `/projects/:id` | Proje detayı | korumalı |
| `/projects/new` | Proje yükleme (bağımsız) | korumalı |
| `*` (403) | 13 Yetkisiz erişim | korumalı |
| oturum bitti | 12 Oturum süresi doldu → `/login` | — |

> `/analysis*`, `/reports*` rotaları ve sidebar'daki "Analizler/Raporlar" hedefleri **#40** tarafından
> aynı `<AppLayout>` altına eklenecek. #39'da sidebar linkleri görünür ama hedef sayfalar #40'a
> bırakılır (yer tutucu veya pasif).

### 8.3 Ortak TypeScript tipleri (API dokümanlarından)
- `User`: `{ id, username, email }` (`GET /api/auth/me/`).
- `Project`: `{ id, name, description, source_type, validation_status, archive: { original_name,
  size_bytes, sha256, uploaded_at }, validation_report, analysis_run_count, created_at, updated_at }`.
- `AnalysisRun` + `AnalysisRunStatus` (9 değerlik enum) + `progress` + `method` (`RULE_BASED |
  DIRECT_LLM | HYBRID`) + `llm_provider` (`GROQ | GEMINI | OLLAMA`).
- `ReferenceRequirement` (iskelet; #40/#41 genişletir).
- `ApiError` zarfları: alan hataları, `{ detail }`, arşiv hata kodları (`ArchiveErrorCode` enum —
  projects.md'deki kodlar), 400/401/403/404/409/413/415/429/500.

### 8.4 Auth ve oturum davranışı (mock)
- Giriş formu Figma'ya göre **"E-posta" etiketi** taşır; backend `username` beklediği için form değeri
  mantıksal olarak "username/e-posta kimliği" alanına eşlenir. Gerçek eşleme #41'de kesinleşir
  (açık soru §11).
- Hesap kilidi: API `429` + sabit mesaj döndürür, `Retry-After`/kalan süre **yok**. Arayüz, kilit
  durumunu ve "3 başarısız denemede 15 dk" bilgisini açıklayan uyarı bileşeni gösterir; kalan süre
  backend vermediği için statik metinle açıklanır (ekran 11).
- Oturum süresi doldu (12): mock'ta manuel tetiklenir; gerçek 401/refresh akışı #41.
- Token saklama yeri (localStorage/bellek) #41'de kesinleşir; #39'da auth-context yalnızca mock
  oturum durumu tutar.

### 8.5 Ekran kapsamı (bu issue)
Giriş (01) · Giriş hatası/kilit (11) · Oturum süresi doldu (12) · Yetkisiz erişim (13) · İlk
kullanım/boş (14) · Genel bakış/dashboard (02) · Projeler (19) · Proje detayı · Proje yükleme
(03'ün bağımsız hali + yeniden kullanılabilir bileşen) · Proje silme onayı (30) · Şifre sıfırlama
(26) · Yeni şifre belirleme · Kullanıcı menüsü (22, Topbar/UserMenu içinde) · Profil (27, temel
görüntüleme + şifre değiştirme formu — mock).

### 8.6 Test yaklaşımı
- **Vitest + React Testing Library.** Kapsam: form doğrulama (giriş, şifre sıfırlama, proje adı),
  korumalı rota yönlendirmesi, `StatusBadge`/`StageStrip` durum eşlemesi, proje listesi boş/dolu/
  yükleniyor/hata durumları, silme onayı akışı, mock servis katmanının imza uyumu.
- Gerçekten çalıştırılıp sonuç raporlanır; çalıştırılmamış test "başarılı" denmez.

### 8.7 Görsel kimlik — "J" (Gece-Sinyal)
Tek kimlik, iki tema. Token'lar `tailwind.config.ts` + CSS değişkenleriyle **merkezi** tutulur; kök
öğedeki `data-theme` (`light` varsayılan / `dark`) değişince tüm arayüz döner. `ThemeToggle` temayı
değiştirir, tercih `localStorage`'da saklanır (ilk ziyarette sistem tercihi başlangıç olabilir).
Tailwind koyu modu `data-theme="dark"` seçicisine bağlanır (`class` yerine attribute tabanlı).

**Fontlar (Google Fonts):** başlık **Space Grotesk**, gövde **Inter**, kod/endpoint/test **JetBrains Mono**.

**Çekirdek token'lar:**

| Rol | Açık (varsayılan) | Koyu |
|---|---|---|
| app-bg / surface | `#f4f8f8` / `#ffffff` | `#0c181b` / `#0f1e22` |
| surface-2 | `#eef5f5` | `#13262b` |
| metin / soluk | `#10262b` / `#53696d` | `#e6f2f2` / `#89a3a6` |
| kenarlık (border / strong) | `#d4e2e2` / `#b6cfd0` | `#1d343a` / `#2a474e` |
| **vurgu (teal)** | `#0f6b7a` | `#3fd0d6` |
| vurgu-soft | `#dceff1` | `#102e30` |
| PASS | `#17935a` (bg `#e4f5ec`) | `#3fc07d` (bg `#0f2a20`) |
| **FAIL (amber / uyarı)** | `#a86a00` (bg `#f8eecd`) | `#f5a524` (bg `#2c2411`) |
| teknik HATA | `#c0392b` (bg `#f8e4e0`) | `#ff5d62` (bg `#2e1518`) |
| süreç | teal (vurgu) | teal (vurgu) |
| kenar menüsü (panel) | koyu teal `#0b2a31`→`#113b45` (iki temada da) | koyu teal `#081013`→`#0f2329` |
| köşe / gölge | radius 8–11px; açıkta yumuşak, koyuda derin gölge | — |

**İmza detaylar:** koyu teal kenar menüsü (iki temada da), aktif menü öğesinde sol teal çizgi, aşama
şeridinde aktif noktada teal parıltı, FAIL etiketinde ince amber çerçeve. **Metrik kartları düz ince
kenarlıktır** — sol renkli şerit YOK (yapay zekâ üretimi tasarım klişesinden kaçınmak için; Reyyan
geri bildirimi). Avatar/rozet metinleri her iki temada da garanti kontrastla (`accent` ↔ `accent-fg`).

**Durum semantiği (J kimliği):** teal = nötr/birincil/süreç · amber = uyarı (FAIL testi) · kırmızı =
teknik/sert hata. Üçlü ayrım bilinçlidir (test FAIL'i ≠ sistem/sandbox hatası).

**Test yürütme ve bulgu renkleri (kanonik modele bağlı — `docs/database`):**
- **TestExecution durumu 8 değer:** `PENDING, RUNNING, PASS, FAIL, ERROR, TIMEOUT, STOPPED, NOT_RUN`.
  **ERROR ile TIMEOUT ayrı gösterilir** (ayrı ton); tek "hata" altında birleştirilmez. PASS yeşil,
  FAIL amber, ERROR kırmızı, TIMEOUT ayrı ton, diğerleri nötr. (Detaylı test sonuçları ekranı #40;
  #39 bu taksonomiyi ortak tip + ton eşlemesi olarak kurar, Reyyan üstüne inşa eder.)
- **SecurityFinding:** `classification` = `VERIFIED/POSSIBLE/UNCERTAIN`, `severity` =
  `HIGH/MEDIUM/LOW/UNKNOWN`. **VERIFIED (doğrulanmış açık) başarı/yeşil ile gösterilMEZ** — kötü bir
  bulgudur; ton severity'ye göre kırmızı/uyarı, POSSIBLE amber, UNCERTAIN nötr.
- **StageStrip kanonik durumlara bağlıdır:** "Rapor" bir `AnalysisRun` durumu değildir; son düğüm
  **"Tamamlandı" (COMPLETED)**. Düğümler: Kuyruk(QUEUED) · Analiz(ANALYZING) · Üretim(GENERATING) ·
  Çalıştırma(EXECUTING) · Tarama(SCANNING) · Tamamlandı(COMPLETED); VALIDATING/FAILED/CANCELLED de
  bileşende ele alınır.
- **Mock hijyeni:** LLM model adı sabit sistem modeli gibi gösterilmez — yalnızca sağlayıcı (ör.
  "Groq") ya da açıkça "örnek"; spesifik model kimliği (ör. "gpt-oss-120b") sabitmiş gibi yazılmaz.

**Önemli:** J yalnızca **kimlik** katmanıdır; ekranların **yapısı, akışı ve bileşenleri Figma'yla
aynıdır.** 31 ekran bu token'ları miras alır; renk/font/tema değişikliği **tek yerden** yapılır
(31 ekran tek tek elden geçirilmez).

## 9. Backend'e göre doğrulanan gerçekler (arayüzü bağlayan)
- Giriş `POST /api/auth/login/` → `{username, password}`; 3 hatada 429 kilit, kalan süre yok.
- Proje oluşturma `POST /api/projects/` yalnızca `multipart/form-data`; alanlar `name` (zorunlu,
  kullanıcı içinde tekil), `description`, `archive` (tek `.zip`, ≤50 MiB → aşımda 413).
- Proje güncelleme yalnızca `name`/`description`; arşiv değiştirilemez.
- Proje silme: aktif analizi varsa 409.
- Analiz oluşturma QUEUED kaydı üretir; Celery başlatmaz (ilerleme `percent` başta `null`).
- **TestExecution durumu 8 değerdir** (`PENDING, RUNNING, PASS, FAIL, ERROR, TIMEOUT, STOPPED,
  NOT_RUN`); `ERROR` ve `TIMEOUT` ayrıdır (`error_type` kısıtı birleştirmeyi yasaklar).
- **SecurityFinding** `classification` (`VERIFIED/POSSIBLE/UNCERTAIN`) + `severity`
  (`HIGH/MEDIUM/LOW/UNKNOWN`); `VERIFIED` başarı değildir, doğrulanmış açıktır.

## 10. Builder'a bırakılanlar
- Figma PNG'lerinden tam boşluk/tipografi ölçeği ve ikon seçimleri.
- Küçük arayüz metinleri (copy).
- Dialog/menü için Radix primitive eklenmesi mi, focus-trap ile elle mi — erişilebilirlik gereğine göre.
- Fixture içerik değerleri (açıkça örnek).
- Mobil kırılım noktalarının ince ayarı.

## 11. Çözülen kararlar
1. **Giriş kimliği:** Form etiketi **"E-posta" kalır** (Figma'ya sadık); değer backend `username`
   alanına eşlenir, nihai eşleme #41'de kesinleşir. (Merve onayı.)
2. **Profil (27):** **#39'a dahil** (mock görüntüleme + şifre değiştirme), kullanıcı menüsünün parçası.
   (Merve onayı.)
3. **Görsel kimlik:** **J (Gece-Sinyal)** — açık varsayılan + koyu mod; fontlar Space Grotesk / Inter /
   JetBrains Mono. (Merve + Reyyan onayı — §6.5, §8.7.)
4. **Figma güncellemesi:** 31 ekranın Figma'da J'ye boyanması **hoca onayına bağlı** (beklemede); kod
   her durumda J olur. Bu issue Figma dosyasını değiştirmez.
