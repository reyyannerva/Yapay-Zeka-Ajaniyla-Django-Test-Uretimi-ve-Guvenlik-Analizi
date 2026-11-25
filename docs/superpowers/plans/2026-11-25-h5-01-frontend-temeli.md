# H5-01 (#39) Frontend Temeli — Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** React + Vite + TS + Tailwind ile, J görsel kimliğinde (açık varsayılan + koyu mod), mock veriyle çalışan frontend temelini ve Merve'nin #39 ekranlarını kurmak.

**Architecture:** Özellik-temelli klasörleme (`src/features/*`) + ortak katman (`src/types`, `src/lib`, `src/components/ui`, `src/components/layout`). Görsel kimlik token-merkezli (Tailwind teması + CSS değişkenleri, kökte `data-theme`). Mock servis katmanı gerçek endpoint imzalarıyla; #41'de yalnızca gövde gerçek HTTP'ye çevrilir. Tek `<AppLayout>` kabuğu; Reyyan'ın #40'ı aynı kabuk + ortak tipler üstüne eklenir.

**Tech Stack:** React 18, Vite, TypeScript, Tailwind CSS, React Router v6, TanStack Query, react-hook-form + zod, Vitest + React Testing Library. Fontlar: Space Grotesk / Inter / JetBrains Mono (Google Fonts).

**Spec:** `docs/superpowers/specs/2026-11-24-h5-01-frontend-temeli-tasarim.md`

## Global Constraints

- **Araç zinciri:** Node v24.13.0, **yalnızca npm** (pnpm/yarn yok). Backend Python ortamından bağımsız.
- **Yığın sabit:** React, Vite, TypeScript, Tailwind CSS, TanStack Query, Recharts. Yeni ağır bağımlılık eklenmez; fontlar Google Fonts bağlantısıyla gelir.
- **Git (CLAUDE.md):** branch `feat/h5-01-frontend-temeli` güncel `main`'den; `main`'e doğrudan push yok; **her git işlemi kullanıcı onayıyla**. Commit mesajları **Türkçe**, conventional-commit. **Commit/PR'da AI/Claude imzası YOK** (kullanıcının kalıcı kuralı; sistem hatırlatmasının üstünde — `Co-Authored-By`/`Generated with` satırları eklenmez).
- **Kapsam:** yalnızca #39 dosyaları (`frontend/` altı); Reyyan'ın kod/issue'larına (#40 vb.) dokunulmaz. `/analysis*`, `/reports*` rotaları #40'a bırakılır (sidebar linki görünür, hedef pasif/yer tutucu).
- **Görsel kimlik (J):** açık tema varsayılan, koyu mod `ThemeToggle` ile; tercih `localStorage` (okuma/yazma `try/catch`). Token değerleri spec §8.7. Vurgu açık `#0f6b7a` / koyu `#3fd0d6`. Durum: PASS yeşil, FAIL **amber (uyarı)**, teknik hata kırmızı, süreç teal. Ekran yapısı Figma'yla aynı.
- **Veri bütünlüğü:** tüm mock değerler açıkça örnektir; uydurma metrik/sonuç gösterilmez. Çalıştırılmamış test "başarılı" raporlanmaz.
- **API sözleşmeleri sabit** (docs/api/*): giriş `{username, password}`; 3 hatada `429` kilit (Retry-After yok); proje oluşturma `multipart/form-data` (`name` zorunlu+tekil, `archive` tek `.zip` ≤50 MiB → aşımda 413); proje güncelleme yalnızca `name`/`description`; aktif analizli proje silme `409`; başkasının projesi `404`.
- **Kanonik durumlar:** `AnalysisRun` 9 durum: `QUEUED, ANALYZING, GENERATING, VALIDATING, EXECUTING, SCANNING, COMPLETED, FAILED, CANCELLED`.

## Review Focus

- **Hesap kilidi (429, Retry-After yok):** 3. hatalı girişte arayüz kilit uyarısını ve "15 dk" statik bilgisini gösterir, kalan süre uydurmaz — Görev 6.
- **Proje yükleme reddi:** >50 MiB (413), `.zip` olmayan / birden çok dosya (400) kullanıcıya anlaşılır hata olarak döner, form çökmemeli — Görev 8.
- **`percent === null`:** yeni/kaydı olmayan analizde ilerleme "%0" değil "henüz veri yok/–" gösterilir — Görev 5 (StageStrip/progress) + Görev 7.
- **Tema kalıcılığı/flash:** `localStorage` erişilemese bile (gizli sekme) tema `try/catch` ile açık varsayılana düşer, ilk boyamada yanlış tema flaş'ı olmaz — Görev 1.
- **Boş ve 403 durumları:** hiç proje yokken ekran 14 boş durumu; başkasının projesine erişimde 403 → ekran 13 — Görev 8 (empty) + Görev 9 (403).

---

### Task 1: Proje iskeleti + J teması + tema değiştirme

**Files:**
- Create: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/tailwind.config.ts`, `frontend/postcss.config.js`, `frontend/index.html`, `frontend/.env.example`, `frontend/.gitignore`
- Create: `frontend/src/main.tsx`, `frontend/src/index.css`, `frontend/src/lib/theme-context.tsx`, `frontend/src/components/ui/ThemeToggle.tsx`
- Create: `frontend/vitest.config.ts`, `frontend/src/test/setup.ts`
- Test: `frontend/src/lib/theme-context.test.tsx`

**Interfaces:**
- Produces: `ThemeProvider` (React context provider), `useTheme(): { theme: 'light' | 'dark'; toggle: () => void }`, `ThemeToggle` bileşeni. Kök `<html>` (veya `#root` sarıcısı) üzerinde `data-theme` attribute'u set edilir. Tailwind koyu modu `data-theme="dark"` seçicisine bağlı.

- [ ] **Step 1: Vite React-TS projesini kur ve bağımlılıkları ekle**

`frontend/` altında npm ile: `react`, `react-dom`, `react-router-dom`, `@tanstack/react-query`, `react-hook-form`, `zod`, `@hookform/resolvers`; dev: `vite`, `@vitejs/plugin-react`, `typescript`, `tailwindcss`, `postcss`, `autoprefixer`, `vitest`, `@testing-library/react`, `@testing-library/user-event`, `@testing-library/jest-dom`, `jsdom`. Sürümler en az iki hafta eski, kararlı sürümler.

- [ ] **Step 2: Tailwind + token temasını yapıla**

`tailwind.config.ts`: `darkMode: ['variant', '&:where([data-theme=dark] *)']`; `theme.extend.colors` CSS değişkenlerine (`var(--accent)` vb.) bağlanır; `fontFamily` display=Space Grotesk, sans=Inter, mono=JetBrains Mono. `index.css`: Google Fonts `@import`/link, `@tailwind` katmanları, `:root[data-theme=light]` ve `:root[data-theme=dark]` için spec §8.7 token değerleri (`--app-bg, --surface, --surface-2, --fg, --muted, --border, --border-strong, --accent, --accent-soft, --pass, --fail, --error, --panel, --panel-2, --panel-fg, --panel-muted`).

- [ ] **Step 3: Tema testini yaz (başarısız)**

```tsx
// theme-context.test.tsx
test('varsayılan açık temadır ve toggle koyuya çevirir', async () => {
  render(<ThemeProvider><ThemeToggle /></ThemeProvider>);
  expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  await userEvent.click(screen.getByRole('button'));
  expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
});
test('tercih localStorage erişilemezse açık temaya düşer (throw yutulur)', () => {
  // localStorage.getItem throw edecek şekilde mock'la
  expect(() => render(<ThemeProvider><ThemeToggle /></ThemeProvider>)).not.toThrow();
  expect(document.documentElement.getAttribute('data-theme')).toBe('light');
});
```

- [ ] **Step 4: Testi çalıştır, başarısız olduğunu gör** — Run: `npm run test -- theme-context` · Expected: FAIL (modül yok).

- [ ] **Step 5: `theme-context.tsx` + `ThemeToggle.tsx` + `main.tsx` uygula**

`ThemeProvider` başlangıç temasını `localStorage` (`try/catch`; yoksa `prefers-color-scheme`, en son `light`) ile belirler, `data-theme`'i köke yazar; `toggle` değeri çevirir ve `try/catch` ile saklar. `ThemeToggle` ay/güneş ikonu + "Koyu tema"/"Açık tema" etiketi gösterir, `toggle` çağırır.

- [ ] **Step 6: Testi çalıştır, geçtiğini gör** — Run: `npm run test -- theme-context` · Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): H5-01 proje iskeleti, J teması ve tema değiştirme"
```

---

### Task 2: Ortak tipler + mock servis katmanı + TanStack Query kurulumu

**Files:**
- Create: `frontend/src/types/{user,project,analysis-run,reference-requirement,api-error,index}.ts`
- Create: `frontend/src/lib/api/{client,auth,projects,analysis-runs}.ts`, `frontend/src/lib/api/mock/{index,projects,analysis-runs}.ts`
- Create: `frontend/src/lib/queryKeys.ts`, `frontend/src/lib/queryClient.ts`
- Test: `frontend/src/lib/api/projects.test.ts`, `frontend/src/lib/queryKeys.test.ts`

**Interfaces:**
- Produces (tipler, spec §8.3 + §9): `User`, `Project`, `PaginatedProjectList`, `AnalysisRun`, `AnalysisRunDetail`, `AnalysisRunStatus` (9-değerlik union), `AnalysisProgress`, `AnalysisMethod`, `LlmProvider`, `ReferenceRequirement`, `ApiError`, `ArchiveErrorCode`, **`TestExecutionStatus`** (8 değer: `PENDING, RUNNING, PASS, FAIL, ERROR, TIMEOUT, STOPPED, NOT_RUN`), **`SecurityFindingClassification`** (`VERIFIED, POSSIBLE, UNCERTAIN`), **`Severity`** (`HIGH, MEDIUM, LOW, UNKNOWN`).
- Produces (servis): `login(c: LoginCredentials): Promise<AuthTokens>`, `logout(): Promise<void>`, `getMe(): Promise<User>`, `requestPasswordReset(email: string): Promise<void>`, `confirmPasswordReset(p: { uid: string; token: string; new_password: string }): Promise<void>`, `listProjects(params?: { page?: number; page_size?: number }): Promise<PaginatedProjectList>`, `getProject(id: string): Promise<Project>`, `createProject(input: ProjectCreateInput): Promise<Project>`, `updateProject(id: string, patch: { name?: string; description?: string }): Promise<Project>`, `deleteProject(id: string): Promise<void>`, `listAnalysisRuns(): Promise<AnalysisRun[]>`, `getAnalysisRun(id: string): Promise<AnalysisRunDetail>`.
- Produces: `queryKeys` (ör. `queryKeys.projects.list(params)`, `queryKeys.projects.detail(id)`, `queryKeys.analysisRuns.list()`, `queryKeys.auth.me()`), `queryClient`.
- Not: `createAnalysisRun` ve analiz oluşturma #40/#41 kapsamıdır; burada tanımlanmaz.

- [ ] **Step 1: Tipleri yaz** — spec §8.3 ve docs/api/* ile birebir. `AnalysisRunStatus` 9 değer; `ArchiveErrorCode` projects.md'deki kod enum'u.

- [ ] **Step 2: Mock fixture ve servis testini yaz (başarısız)**

```ts
// projects.test.ts
test('listProjects sayfalı tip döndürür ve en yeni önce gelir', async () => {
  const page = await listProjects();
  expect(page).toHaveProperty('count');
  expect(Array.isArray(page.results)).toBe(true);
  expect(page.results[0]).toHaveProperty('validation_status');
});
test('createProject verilen adla Project döndürür', async () => {
  const p = await createProject({ name: 'Örnek', description: '', archive: new File([], 'x.zip') });
  expect(p.name).toBe('Örnek');
  expect(p.id).toBeTruthy();
});
// queryKeys.test.ts
test('queryKeys kararlı ve ayırt edicidir', () => {
  expect(queryKeys.projects.detail('1')).toEqual(queryKeys.projects.detail('1'));
  expect(queryKeys.projects.detail('1')).not.toEqual(queryKeys.projects.detail('2'));
});
```

- [ ] **Step 3: Testleri çalıştır, başarısız gör** — Run: `npm run test -- lib/` · Expected: FAIL.

- [ ] **Step 4: `client.ts`, mock fixture'ları ve servis fonksiyonlarını uygula**

`client.ts` imzalı fetch sarıcı (`apiFetch<T>(path, init): Promise<T>`) — gövdesi #41'de dolacak, şimdilik kullanılmıyor. Servis fonksiyonları `mock/` fixture'larını `Promise.resolve` ile döndürür; fixture'lar açıkça örnek veridir ve tiplere uyar. `queryKeys` ve `queryClient` tanımlanır.

- [ ] **Step 5: Testleri çalıştır, geçtiğini gör** — Run: `npm run test -- lib/` · Expected: PASS.

- [ ] **Step 6: Commit** — `git commit -m "feat(frontend): ortak tipler, mock servis katmanı ve query kurulumu"`

---

### Task 3: Auth bağlamı (mock) + korumalı rota + AppLayout kabuğu

**Files:**
- Create: `frontend/src/lib/auth-context.tsx`
- Create: `frontend/src/components/layout/{AppLayout,Sidebar,Topbar,UserMenu,ProtectedRoute}.tsx`
- Create: `frontend/src/App.tsx` (rota iskeleti), güncelle: `frontend/src/main.tsx` (Router + QueryClientProvider + ThemeProvider + AuthProvider)
- Test: `frontend/src/components/layout/ProtectedRoute.test.tsx`, `frontend/src/components/layout/AppLayout.test.tsx`

**Interfaces:**
- Consumes: Görev 1 `ThemeProvider`/`ThemeToggle`, Görev 2 `getMe`/`logout`/`queryClient`.
- Produces: `AuthProvider`, `useAuth(): { user: User | null; isAuthenticated: boolean; signInMock: (u: User) => void; signOut: () => void; expireSession: () => void }`; `ProtectedRoute` (kimliksizse `/login`'e yönlendirir); `AppLayout` (Sidebar + Topbar + `<Outlet/>`); Sidebar linkleri: Genel bakış, Projeler, Analizler (pasif/#40), Raporlar (pasif/#40).

- [ ] **Step 1: Testleri yaz (başarısız)**

```tsx
// ProtectedRoute.test.tsx
test('kimliksiz kullanıcı /login\'e yönlenir', () => {
  renderWithRouter(['/dashboard'], { authenticated: false });
  expect(screen.getByTestId('login-route')).toBeInTheDocument();
});
test('kimlikli kullanıcı korunan içeriği görür', () => {
  renderWithRouter(['/dashboard'], { authenticated: true });
  expect(screen.getByTestId('dashboard-route')).toBeInTheDocument();
});
// AppLayout.test.tsx
test('kenar menüsü ana linkleri ve tema düğmesini içerir', () => {
  renderLayout();
  expect(screen.getByRole('link', { name: /Projeler/ })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /tema/i })).toBeInTheDocument();
});
```

- [ ] **Step 2: Çalıştır, başarısız gör** — Run: `npm run test -- layout/` · Expected: FAIL.

- [ ] **Step 3: `auth-context`, `ProtectedRoute`, `AppLayout`/`Sidebar`/`Topbar`/`UserMenu` uygula** — Topbar `ThemeToggle` + UserMenu içerir; `main.tsx` sağlayıcıları sarar; `App.tsx` rota iskeletini (yer tutucu sayfalar) tanımlar.

- [ ] **Step 4: Çalıştır, geç** — Run: `npm run test -- layout/` · Expected: PASS.

- [ ] **Step 5: Commit** — `git commit -m "feat(frontend): mock auth, korumalı rota ve AppLayout kabuğu"`

---

### Task 4: Ortak UI primitifleri

**Files:**
- Create: `frontend/src/components/ui/{Button,Input,Card,Spinner,EmptyState,Toast}.tsx`
- Test: `frontend/src/components/ui/{Button,Input,EmptyState}.test.tsx`

**Interfaces:**
- Produces: `Button` (`variant?: 'primary' | 'ghost'`, `block?`, native button props), `Input` (label, error, react-hook-form `register` uyumlu `forwardRef`), `Card`, `Spinner`, `EmptyState` (`title`, `description`, `action?`), `Toast`/`useToast`.

- [ ] **Step 1: Testleri yaz (başarısız)** — `Button` tıklanınca `onClick` çağrılır ve `disabled`'ken çağrılmaz; `Input` `error` verince hata metnini ve `aria-invalid` gösterir; `EmptyState` başlık + aksiyon render eder.

- [ ] **Step 2: Çalıştır, başarısız gör** — Run: `npm run test -- ui/` · Expected: FAIL.

- [ ] **Step 3: Bileşenleri token sınıflarıyla uygula** (renk/köşe/gölge yalnızca token sınıflarından; sabit renk yazılmaz).

- [ ] **Step 4: Çalıştır, geç** — Expected: PASS.

- [ ] **Step 5: Commit** — `git commit -m "feat(frontend): ortak UI primitifleri (Button, Input, Card, EmptyState, Toast, Spinner)"`

---

### Task 5: Durum ve veri bileşenleri

**Files:**
- Create: `frontend/src/components/ui/{StatusBadge,StageStrip,MetricCard,DataTable,Modal,ConfirmDialog}.tsx`
- Create: `frontend/src/lib/analysis-status.ts` (durum → etiket/renk/sınıf eşlemesi)
- Test: `frontend/src/components/ui/{StatusBadge,StageStrip,DataTable}.test.tsx`

**Interfaces:**
- Consumes: Görev 2 `AnalysisRunStatus`, `AnalysisProgress`, `TestExecutionStatus`, `SecurityFindingClassification`, `Severity`.
- Produces:
  - `STATUS_META: Record<AnalysisRunStatus, { label; tone: 'pass'|'process'|'error'|'muted' }>`; `StatusBadge({ status })`.
  - `TEST_STATUS_META: Record<TestExecutionStatus, { label; tone: 'pass'|'fail'|'error'|'timeout'|'muted' }>` — **ERROR ve TIMEOUT ayrı ton**; `TestStatusBadge({ status })`.
  - `FINDING_META` (classification + severity → ton); `FindingBadge({ classification, severity })` — **VERIFIED asla 'pass'/yeşil değil** (severity'ye göre kırmızı/uyarı; POSSIBLE amber; UNCERTAIN nötr).
  - `StageStrip({ status, progress })` — **kanonik durumlara** bağlı; son düğüm "Tamamlandı" (COMPLETED), "Rapor" aşaması YOK; `percent === null` iken yüzde göstermez.
  - `MetricCard({ label, value, hint?, alert? })` — **düz ince kenarlık** (sol renkli şerit yok).
  - `DataTable<T>({ columns, rows, emptyState })`; `Modal`, `ConfirmDialog`.

- [ ] **Step 1: Testleri yaz (başarısız)**

```tsx
test('StatusBadge 9 durumun tümünü eşler', () => {
  (['QUEUED','ANALYZING','GENERATING','VALIDATING','EXECUTING','SCANNING','COMPLETED','FAILED','CANCELLED'] as const)
    .forEach(s => { render(<StatusBadge status={s} />); expect(screen.getByText(STATUS_META[s].label)).toBeInTheDocument(); });
});
test('TestStatusBadge ERROR ile TIMEOUT\'u farklı tonda gösterir', () => {
  expect(TEST_STATUS_META.ERROR.tone).not.toBe(TEST_STATUS_META.TIMEOUT.tone);
  render(<><TestStatusBadge status="ERROR" /><TestStatusBadge status="TIMEOUT" /></>);
  expect(screen.getByText(TEST_STATUS_META.ERROR.label)).toBeInTheDocument();
  expect(screen.getByText(TEST_STATUS_META.TIMEOUT.label)).toBeInTheDocument();
});
test('FindingBadge VERIFIED başarı/yeşil tonu kullanmaz', () => {
  expect(FINDING_META.VERIFIED.tone).not.toBe('pass');
  render(<FindingBadge classification="VERIFIED" severity="HIGH" />);
  expect(screen.getByText(/doğrulan/i)).toBeInTheDocument();
});
test('StageStrip son düğüm "Tamamlandı"dır, "Rapor" aşaması yoktur', () => {
  render(<StageStrip status="COMPLETED" progress={{ total: 34, percent: 100 }} />);
  expect(screen.getByText(/Tamamlandı/)).toBeInTheDocument();
  expect(screen.queryByText(/^Rapor$/)).not.toBeInTheDocument();
});
test('StageStrip percent null iken yüzde göstermez, "henüz veri yok" der', () => {
  render(<StageStrip status="QUEUED" progress={{ total: 0, percent: null }} />);
  expect(screen.queryByText('%0')).not.toBeInTheDocument();
  expect(screen.getByText(/henüz/i)).toBeInTheDocument();
});
test('DataTable boş satırda emptyState gösterir', () => {
  render(<DataTable columns={[]} rows={[]} emptyState={<div>Boş</div>} />);
  expect(screen.getByText('Boş')).toBeInTheDocument();
});
```

- [ ] **Step 2: Çalıştır, başarısız gör** — Expected: FAIL.

- [ ] **Step 3: `analysis-status.ts` + bileşenleri uygula** — AnalysisRun: süreç/aktif teal, FAIL amber, COMPLETED yeşil. TestExecution: PASS yeşil, FAIL amber, **ERROR kırmızı ≠ TIMEOUT (ayrı ton)**. Finding: **VERIFIED severity'ye göre kırmızı/uyarı (yeşil değil)**, POSSIBLE amber, UNCERTAIN nötr. StageStrip kanonik durumlara bağlı, son düğüm "Tamamlandı", `percent === null` → "henüz veri yok/–". MetricCard **düz ince kenarlık** (sol renkli şerit yok).

- [ ] **Step 4: Çalıştır, geç** — Expected: PASS.

- [ ] **Step 5: Commit** — `git commit -m "feat(frontend): durum/veri bileşenleri (StatusBadge, StageStrip, MetricCard, DataTable, Modal)"`

---

### Task 6: Kimlik doğrulama ekranları

**Files:**
- Create: `frontend/src/features/auth/{Login,ForgotPassword,ResetPassword,SessionExpired}.tsx`
- Create: `frontend/src/features/auth/useLoginForm.ts` (zod şema + react-hook-form)
- Güncelle: `frontend/src/App.tsx` (public rotalar)
- Test: `frontend/src/features/auth/{Login,ResetPassword}.test.tsx`

**Interfaces:**
- Consumes: Görev 2 `login`/`requestPasswordReset`/`confirmPasswordReset`, Görev 4 `Button`/`Input`, Görev 3 `useAuth`.
- Produces: `/login`, `/forgot-password`, `/reset-password` sayfaları; giriş hatası + hesap kilidi inline (ekran 11); oturum süresi doldu (12) görünümü.

- [ ] **Step 1: Testleri yaz (başarısız)**

```tsx
test('boş form zorunlu alan hatası gösterir', async () => {
  renderLogin(); await userEvent.click(screen.getByRole('button', { name: /Giriş/ }));
  expect(await screen.findByText(/zorunlu/i)).toBeInTheDocument();
});
test('3. hatalı denemede kilit uyarısı ve 15 dk bilgisi gösterilir, kalan süre uydurulmaz', async () => {
  renderLogin({ failUntilLock: true });
  // 3 başarısız deneme sonrası:
  expect(await screen.findByText(/geçici olarak kilitlendi|15 dk/i)).toBeInTheDocument();
  expect(screen.queryByText(/kalan süre: \d/i)).not.toBeInTheDocument();
});
test('form "E-posta" etiketi gösterir (değer username\'e eşlenir)', () => {
  renderLogin(); expect(screen.getByLabelText(/E-posta/)).toBeInTheDocument();
});
```

- [ ] **Step 2: Çalıştır, başarısız gör** — Expected: FAIL.

- [ ] **Step 3: Ekranları uygula** — `useLoginForm` zod ile doğrular; mock `login` 3. denemede `429` kilit senaryosu simüle eder; etiket "E-posta", değer `username`'e eşlenir; ResetPassword `uid/token` query okur; SessionExpired `/login`'e yönlendirme sunar.

- [ ] **Step 4: Çalıştır, geç** — Expected: PASS.

- [ ] **Step 5: Commit** — `git commit -m "feat(frontend): giriş, şifre sıfırlama ve oturum sonu ekranları"`

---

### Task 7: Dashboard / Genel bakış (ekran 02)

**Files:**
- Create: `frontend/src/features/dashboard/Overview.tsx`, `frontend/src/features/dashboard/useOverviewData.ts`
- Güncelle: `frontend/src/App.tsx` (`/dashboard` korumalı rota)
- Test: `frontend/src/features/dashboard/Overview.test.tsx`

**Interfaces:**
- Consumes: Görev 2 `listProjects`/`listAnalysisRuns`, Görev 5 `MetricCard`/`StageStrip`/`DataTable`/`StatusBadge`, TanStack Query.
- Produces: `/dashboard` sayfası; metrik kartları, devam eden analiz aşama şeridi, son analizler tablosu.

- [ ] **Step 1: Testini yaz (başarısız)** — yüklenirken `Spinner`; yüklenince ≥1 `MetricCard` ve son analizler tablosunda mock satırlar; devam eden analiz için `StageStrip` görünür.

- [ ] **Step 2: Çalıştır, başarısız gör** — Expected: FAIL.

- [ ] **Step 3: `useOverviewData` (query'ler) + `Overview` uygula** — metrik değerleri mock servisten; açıkça örnek. **Doğrulanmış bulgular `FindingBadge` ile (yeşil/başarı tonu DEĞİL).** Son analizler satırında LLM **yalnızca sağlayıcı** ("Groq") veya "örnek" gösterilir; spesifik model kimliği sabitmiş gibi yazılmaz. Devam eden analizde `StageStrip` (son düğüm "Tamamlandı").

- [ ] **Step 4: Çalıştır, geç** — Expected: PASS.

- [ ] **Step 5: Commit** — `git commit -m "feat(frontend): genel bakış (dashboard) ekranı"`

---

### Task 8: Proje yönetimi (liste, detay, yükleme, düzenleme, silme)

**Files:**
- Create: `frontend/src/features/projects/{ProjectList,ProjectDetail,ProjectUpload,ProjectEdit,DeleteConfirm}.tsx`
- Create: `frontend/src/features/projects/useProjectForm.ts` (zod: `name` zorunlu, arşiv `.zip` + boyut doğrulaması)
- Güncelle: `frontend/src/App.tsx` (`/projects`, `/projects/:id`, `/projects/new`)
- Test: `frontend/src/features/projects/{ProjectList,ProjectUpload,DeleteConfirm}.test.tsx`

**Interfaces:**
- Consumes: Görev 2 proje servisleri, Görev 4/5 UI, Görev 3 AppLayout.
- Produces: `/projects` (ekran 19 + boş durum 14), `/projects/:id`, `/projects/new`; **yeniden kullanılabilir `ProjectUpload` bileşeni** (#40'ın "Yeni analiz" sihirbazı adım 1'de kullanacak — spec §7); silme onayı (ekran 30, 409 durumu).

- [ ] **Step 1: Testleri yaz (başarısız)**

```tsx
test('hiç proje yokken boş durum (14) gösterilir', async () => {
  renderList({ projects: [] });
  expect(await screen.findByText(/ilk projenizi|henüz proje yok/i)).toBeInTheDocument();
});
test('50 MiB üstü arşiv seçilince boyut hatası gösterilir, form çökmez', async () => {
  renderUpload();
  await selectFile(bigZip /* >50 MiB */);
  expect(await screen.findByText(/en fazla 50 ?MiB|boyut/i)).toBeInTheDocument();
});
test('.zip olmayan dosya reddedilir', async () => {
  renderUpload(); await selectFile(new File([], 'x.tar'));
  expect(await screen.findByText(/\.zip/i)).toBeInTheDocument();
});
test('aktif analizli proje silinmeye çalışılınca 409 mesajı gösterilir', async () => {
  renderDelete({ conflict: true }); await userEvent.click(screen.getByRole('button', { name: /Sil/ }));
  expect(await screen.findByText(/devam eden bir analizi/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Çalıştır, başarısız gör** — Expected: FAIL.

- [ ] **Step 3: Ekranları + `useProjectForm` uygula** — istemci tarafı doğrulama (zod): `.zip` uzantısı/tip, ≤50 MiB; sunucu reddi (400/413/409) mock'ta simüle edilip anlaşılır mesaja çevrilir; `ProjectUpload` bağımsız ve yeniden kullanılabilir.

- [ ] **Step 4: Çalıştır, geç** — Expected: PASS.

- [ ] **Step 5: Commit** — `git commit -m "feat(frontend): proje listesi, detay, yükleme, düzenleme ve silme"`

---

### Task 9: Durum ekranları (403 yetkisiz, oturum sonu bağlama)

**Files:**
- Create: `frontend/src/features/status/{Unauthorized,NotFound}.tsx`
- Güncelle: `frontend/src/App.tsx` (403 → ekran 13, `*` → NotFound), `Topbar`/`auth-context` (oturum sonu akışı → 12 → `/login`)
- Test: `frontend/src/features/status/Unauthorized.test.tsx`

**Interfaces:**
- Consumes: Görev 3 `useAuth`, AppLayout.
- Produces: 13 yetkisiz erişim, 12 oturum süresi doldu yönlendirmesi; başkasının projesine erişim (mock 404/403) 13'e düşer.

- [ ] **Step 1: Testini yaz (başarısız)** — başkasının projesi (mock 403/404) açılınca Unauthorized (13) görünür; "Panele dön" linki `/dashboard`'a gider.

- [ ] **Step 2: Çalıştır, başarısız gör** — Expected: FAIL.

- [ ] **Step 3: Ekranları + yönlendirmeyi uygula.**

- [ ] **Step 4: Çalıştır, geç** — Expected: PASS.

- [ ] **Step 5: Commit** — `git commit -m "feat(frontend): yetkisiz erişim ve durum ekranları"`

---

### Task 10: Profil (ekran 27)

**Files:**
- Create: `frontend/src/features/profile/Profile.tsx`, `frontend/src/features/profile/usePasswordChangeForm.ts`
- Güncelle: `frontend/src/App.tsx` (`/profile`), `UserMenu` (Profil linki)
- Test: `frontend/src/features/profile/Profile.test.tsx`

**Interfaces:**
- Consumes: Görev 2 `getMe`, Görev 4 UI.
- Produces: `/profile` — hesap bilgisi görüntüleme (ad/e-posta salt-okunur, yönetici günceller) + şifre değiştirme formu (mock).

- [ ] **Step 1: Testini yaz (başarısız)** — profil kullanıcı bilgisini gösterir; şifre formunda yeni şifre doğrulaması (boş/zayıf) hata verir.

- [ ] **Step 2: Çalıştır, başarısız gör** — Expected: FAIL.

- [ ] **Step 3: Ekranı uygula.**

- [ ] **Step 4: Çalıştır, geç** — Expected: PASS.

- [ ] **Step 5: Commit** — `git commit -m "feat(frontend): profil ekranı ve şifre değiştirme formu"`

---

### Task 11: Tüm paketi doğrula + ekran görüntüleri + çalıştırma yönergeleri

**Files:**
- Create: `frontend/README.md`, `docs/mockup/j-kimligi/` (açık/koyu ekran görüntüleri)
- Güncelle: gerekiyorsa `frontend/package.json` script'leri (`dev`, `build`, `test`, `lint`)

- [ ] **Step 1: Tüm testleri çalıştır** — Run: `npm run test` · Expected: hepsi PASS (gerçek çıktı rapora yazılır; geçmeyen varsa düzeltilir, "başarılı" uydurulmaz).

- [ ] **Step 2: Üretim derlemesini doğrula** — Run: `npm run build` · Expected: hatasız derleme.

- [ ] **Step 3: Uygulamayı çalıştırıp açık ve koyu temada giriş + dashboard + proje yükleme ekranlarının görüntülerini al**, `docs/mockup/j-kimligi/` altına koy. **Kontrast denetimi:** kenar menüsündeki avatar baş harfleri her iki temada okunur (zemin `accent`, metin `accent-fg`); okunmuyorsa düzelt.

- [ ] **Step 4: `frontend/README.md` yaz** — kurulum (`npm install`), çalıştırma (`npm run dev`), test (`npm run test`), tema notu, mock veri uyarısı, #41 (gerçek API) ve #40 (analiz ekranları) sınırları.

- [ ] **Step 5: Commit** — `git commit -m "docs(frontend): çalıştırma yönergeleri ve J kimliği ekran görüntüleri"`

---

## Kapsam dışı (sonraki issue'lar)
- Gerçek HTTP/JWT entegrasyonu, token saklama, 401/refresh — **#41**.
- Analiz ayarları/endpointler/üretilen testler/sonuçlar/bulgular/rapor, "Yeni analiz" sihirbazı, referans gereksinimler — **#40** (Reyyan).
- Recharts grafikleri — #40/#43.
- Figma dosyasının J'ye güncellenmesi — hoca onayına bağlı, ayrı iş.
