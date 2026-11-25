// H5-03 / #41 — Gerçek uçtan uca entegrasyon testleri.
// Gerçek tarayıcı (Chromium) + Vite frontend + Django/DRF backend + PostgreSQL + yerel SMTP yakalayıcı.
// API yolları taklit EDİLMEZ; tek istisna yoktur. Backend bu betik tarafından başlatılır/durdurulur
// (bağlantı kesintisi ve yeniden başlatma sonrası kalıcılık senaryoları için).
// Ayrıntı ve çalıştırma: e2e/h5-03/README.md (run.sh).
'use strict';

const { chromium } = require('playwright');
const { spawn, execFileSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '../..');
const BACKEND = path.join(ROOT, 'backend');
const FRONT = process.env.E2E_FRONT_URL || 'http://localhost:5173';
const API = process.env.E2E_API_URL || 'http://127.0.0.1:8000';
const CREDS = JSON.parse(fs.readFileSync(process.env.E2E_CREDS, 'utf8'));
const FIXTURES = process.env.E2E_FIXTURES;
const MAIL_DIR = process.env.E2E_MAIL_DIR;
const SHOTS = process.env.E2E_SHOTS || path.join(ROOT, 'docs/mockup/h5-03');
const EVIDENCE = process.env.E2E_EVIDENCE || path.join(ROOT, 'docs/integration/h5-03');
const BACKEND_ENV = { ...process.env, ...JSON.parse(process.env.E2E_BACKEND_ENV || '{}') };

fs.mkdirSync(SHOTS, { recursive: true });
fs.mkdirSync(EVIDENCE, { recursive: true });

const results = [];
const apiExamples = [];
const consoleIssues = [];
let backend = null;

// ---------------------------------------------------------------- yardımcılar
function log(message) {
  process.stdout.write(`${message}\n`);
}

async function step(id, title, fn) {
  const started = Date.now();
  try {
    const detail = await fn();
    results.push({ id, title, status: 'PASS', detail: detail ?? null, ms: Date.now() - started });
    log(`PASS ${id} ${title}`);
  } catch (error) {
    results.push({ id, title, status: 'FAIL', detail: String(error && error.message ? error.message : error), ms: Date.now() - started });
    log(`FAIL ${id} ${title}: ${error && error.message}`);
  }
}

function expect(condition, message) {
  if (!condition) throw new Error(message);
}

function probe(...args) {
  const out = execFileSync('python', [path.join(__dirname, 'db_probe.py'), ...args.map(String)], {
    cwd: BACKEND,
    env: BACKEND_ENV,
    encoding: 'utf8',
  });
  return JSON.parse(out.trim().split('\n').pop());
}

function startBackend() {
  backend = spawn('python', ['manage.py', 'runserver', '127.0.0.1:8000', '--noreload'], {
    cwd: BACKEND,
    env: BACKEND_ENV,
    stdio: ['ignore', 'ignore', 'pipe'],
  });
  backend.stderr.on('data', () => {});
}

async function waitForBackend(up = true) {
  for (let i = 0; i < 60; i += 1) {
    try {
      const res = await fetch(`${API}/api/auth/me/`);
      if (up && res.status === 401) return;
    } catch {
      if (!up) return;
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error(`backend ${up ? 'başlamadı' : 'durmadı'}`);
}

async function stopBackend() {
  if (!backend) return;
  backend.kill('SIGTERM');
  await new Promise((r) => backend.once('exit', r));
  backend = null;
}

const SENSITIVE = /^(access|refresh|password|new_password|token|uid)$/;
function redact(value) {
  if (Array.isArray(value)) return value.map(redact);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, SENSITIVE.test(k) ? '<redakte>' : redact(v)]));
  }
  return value;
}

function recordApi(page) {
  // `response` olayı kullanılır: Chrome 205 (Reset Content) yanıtlarında `requestfinished` tetiklemez.
  page.on('response', async (response) => {
    const request = response.request();
    const url = new URL(request.url());
    if (!url.pathname.startsWith('/api/')) return;
    try {
      const status = response.status();
      const pattern = url.pathname.replace(/\/\d+\//g, '/{id}/');
      const key = `${request.method()} ${pattern} ${status}`;
      if (apiExamples.some((e) => e.key === key)) return;
      let requestBody = null;
      const type = request.headers()['content-type'] || '';
      if (type.includes('multipart/form-data')) {
        requestBody = 'multipart/form-data (name, description, archive=<ZIP dosyası>)';
      } else if (request.postData()) {
        try {
          requestBody = redact(JSON.parse(request.postData()));
        } catch {
          requestBody = '<JSON değil>';
        }
      }
      let responseBody = null;
      if (status !== 204 && status !== 205) {
        try {
          responseBody = redact(await response.json());
        } catch {
          responseBody = null;
        }
      }
      apiExamples.push({
        key,
        method: request.method(),
        endpoint: pattern + (url.search ? url.search.replace(/=[^&]+/g, '=…') : ''),
        status,
        authorization: request.headers().authorization ? 'Bearer <redakte>' : 'yok',
        request: requestBody,
        response: responseBody,
        retry_after: response.headers()['retry-after'] || undefined,
      });
    } catch {
      /* sayfa kapanırken gelen olaylar yok sayılır */
    }
  });
}

async function newPage(browser, viewport = { width: 1440, height: 900 }) {
  const context = await browser.newContext({ viewport, deviceScaleFactor: 2, acceptDownloads: true });
  const page = await context.newPage();
  page.on('console', (m) => {
    if (m.type() === 'error' || m.type() === 'warning') consoleIssues.push(`${m.type()}: ${m.text()}`);
  });
  page.on('pageerror', (e) => consoleIssues.push(`pageerror: ${e.message}`));
  recordApi(page);
  return page;
}

async function login(page, user, password = user.password) {
  // Temiz bir geçmiş kaydı: önceki yönlendirmenin `state.from` değeri taşınmaz.
  await page.goto('about:blank');
  await page.goto(`${FRONT}/login`);
  await page.getByLabel('Kullanıcı adı').fill(user.username);
  await page.getByLabel('Parola').fill(password);
  await page.getByRole('button', { name: 'Giriş yap' }).click();
}

async function shot(page, name, options = {}) {
  await page.waitForTimeout(250);
  await page.screenshot({ path: path.join(SHOTS, `${name}.png`), fullPage: true, ...options });
}

async function nav(page, to) {
  // İstemci tarafı gezinme (sayfa yenileme ayrıca test edilir).
  await page.evaluate((p) => {
    window.history.pushState({}, '', p);
    window.dispatchEvent(new PopStateEvent('popstate'));
  }, to);
  await page.waitForTimeout(500);
}

async function uploadProject(page, name, description = '') {
  await page.goto(`${FRONT}/projects/new`);
  await page.getByLabel('Proje adı').fill(name);
  if (description) await page.getByLabel('Açıklama (isteğe bağlı)').fill(description);
  await page.getByLabel('Proje arşivi').setInputFiles(path.join(FIXTURES, 'ornek_api.zip'));
  await page.getByRole('button', { name: 'Projeyi yükle' }).click();
  await page.waitForURL(/\/projects\/\d+$/, { timeout: 20000 });
  return Number(page.url().split('/').pop());
}

function latestMail(after) {
  const files = fs.readdirSync(MAIL_DIR).filter((f) => f.endsWith('.eml')).map((f) => path.join(MAIL_DIR, f));
  const fresh = files.filter((f) => fs.statSync(f).mtimeMs >= after).sort();
  return fresh.length ? fs.readFileSync(fresh[fresh.length - 1], 'utf8') : null;
}

// ---------------------------------------------------------------- senaryolar
(async () => {
  const runTag = Date.now().toString(36);
  const A = CREDS.A;
  const B = CREDS.B;
  const C = CREDS.C;
  const state = {};

  startBackend();
  await waitForBackend(true);
  const browser = await chromium.launch();

  await step('ENV-1', 'Backend veritabanı gerçekten PostgreSQL', async () => {
    const info = probe('backend');
    expect(info.vendor === 'postgresql', `vendor=${info.vendor}`);
    return info;
  });

  // ---- Ana senaryo (Issue #41 E2E 1–25) ----
  const page = await newPage(browser);
  await step('E2E-01-02', 'Login ekranı açılır, gerçek kullanıcı A ile giriş yapılır', async () => {
    await login(page, A);
    await page.waitForURL(/\/dashboard$/, { timeout: 15000 });
  });
  await step('E2E-03', 'Dashboard gerçek API verisiyle görüntülenir', async () => {
    await page.getByRole('region', { name: 'Metrikler' }).waitFor();
    expect(!(await page.getByText('Örnek veri').count()), 'dashboard "Örnek veri" etiketi taşımamalı');
    await shot(page, '01-giris-sonrasi-dashboard');
  });

  const projectName = `E2E Sipariş API ${runTag}`;
  await step('E2E-04', 'Gerçek ZIP arşivi multipart ile yüklenir; PostgreSQL kaydı A kullanıcısına aittir', async () => {
    await page.goto(`${FRONT}/projects/new`);
    await page.getByLabel('Proje adı').fill(projectName);
    await page.getByLabel('Açıklama (isteğe bağlı)').fill('Uçtan uca test projesi');
    await page.getByLabel('Proje arşivi').setInputFiles(path.join(FIXTURES, 'ornek_api.zip'));
    await shot(page, '07-proje-yukleme');
    await page.getByRole('button', { name: 'Projeyi yükle' }).click();
    await page.waitForURL(/\/projects\/\d+$/, { timeout: 20000 });
    state.projectId = Number(page.url().split('/').pop());
    const db = probe('project', state.projectId);
    expect(db.exists && db.owner === A.username && db.name === projectName, JSON.stringify(db));
    return db;
  });
  await step('E2E-04b', 'Geçersiz arşiv (bozuk ZIP) sunucu tarafından reddedilir ve kaydedilmez', async () => {
    await page.goto(`${FRONT}/projects/new`);
    await page.getByLabel('Proje adı').fill(`Bozuk ${runTag}`);
    await page.getByLabel('Proje arşivi').setInputFiles(path.join(FIXTURES, 'bozuk.zip'));
    await page.getByRole('button', { name: 'Projeyi yükle' }).click();
    await page.getByText(/ZIP arşivi değil|bozuk görünüyor|Arşiv/).first().waitFor({ timeout: 10000 });
    expect(page.url().endsWith('/projects/new'), 'bozuk arşivde yönlendirme olmamalı');
  });
  await step('E2E-05-06', 'Proje listesinde gerçek proje görünür', async () => {
    await page.goto(`${FRONT}/projects`);
    await page.getByRole('link', { name: projectName }).waitFor();
    await shot(page, '08-proje-listesi');
  });
  await step('E2E-07', 'Proje detayı açılır', async () => {
    await page.getByRole('link', { name: projectName }).click();
    await page.getByRole('heading', { name: projectName }).waitFor();
    await shot(page, '09-proje-detay');
  });
  await step('E2E-08-10', 'Proje güncellenir; sayfa yenilemede ve PostgreSQL\'de korunur', async () => {
    await page.getByRole('link', { name: 'Düzenle' }).click();
    await page.getByLabel('Açıklama (isteğe bağlı)').fill('Açıklama güncellendi (E2E)');
    await page.getByRole('button', { name: 'Kaydet' }).click();
    await page.waitForURL(new RegExp(`/projects/${state.projectId}$`));
    await page.reload();
    await page.getByText('Açıklama güncellendi (E2E)').waitFor({ timeout: 10000 });
    const db = probe('project', state.projectId);
    expect(db.description === 'Açıklama güncellendi (E2E)', JSON.stringify(db));
    await shot(page, '10-proje-guncelleme-sonrasi');
    return db;
  });
  await step('E2E-14-15', 'Geçerli referans JSON kaydedilir; yenilemeden sonra backend\'den okunur', async () => {
    await page.getByRole('button', { name: 'JSON yükle' }).click();
    await page.locator('input[type=file][accept*=json]').setInputFiles(path.join(FIXTURES, 'gecerli_referans.json'));
    await page.getByRole('button', { name: 'Doğrula ve kaydet' }).click();
    await page.getByRole('button', { name: 'ACC-SIPARIS-1' }).waitFor({ timeout: 10000 });
    await page.reload();
    await page.getByRole('button', { name: 'ACC-SIPARIS-1' }).click();
    await page.getByLabel('ACC-SIPARIS-1 JSON').waitFor();
    const db = probe('requirements', state.projectId);
    expect(db.items.length === 2 && db.items.some((i) => i.method === 'GET' && i.source === 'JSON_UPLOAD'), JSON.stringify(db));
    await page.getByRole('region', { name: 'Referans gereksinimler' }).screenshot({ path: path.join(SHOTS, '13-referans-json-goruntuleme.png') });
    return db.items.map((i) => ({ code: i.code, method: i.method, revision: i.revision }));
  });
  await step('E2E-16', 'Geçersiz referans JSON (TRACE metodu) reddedilir; PostgreSQL\'e yazılmaz', async () => {
    await page.getByRole('button', { name: 'JSON yükle' }).click();
    await page.locator('input[type=file][accept*=json]').setInputFiles(path.join(FIXTURES, 'gecersiz_referans.json'));
    await page.getByRole('button', { name: 'Doğrula ve kaydet' }).click();
    await page.getByTestId('requirement-issues').waitFor();
    const text = await page.getByTestId('requirement-issues').innerText();
    expect(/specification\.method/.test(text), text);
    await page.getByRole('region', { name: 'Referans gereksinimler' }).screenshot({ path: path.join(SHOTS, '14-gecersiz-referans-json.png') });
    expect(probe('requirement-count', 'ACC-HATALI').count === 0, 'geçersiz kayıt veritabanına yazılmamalı');
    // Sunucu tarafı doğrulama: istemciden geçen ama sunucunun reddettiği kayıt (yinelenen kod).
    await page.getByLabel(/JSON \(tek nesne/).fill(fs.readFileSync(path.join(FIXTURES, 'gecerli_referans.json'), 'utf8'));
    await page.getByRole('button', { name: 'Doğrula ve kaydet' }).click();
    await page.getByText(/sunucu tarafından reddedildi|Sunucu kayıtları reddetti/).waitFor();
    expect(probe('requirements', state.projectId).items.length === 2, 'yinelenen kayıt eklenmemeli');
    await page.getByRole('button', { name: 'Vazgeç' }).click();
  });
  await step('E2E-11-13', 'Gerçek AnalysisRun oluşturulur; liste/detay gerçek durumu (QUEUED) gösterir', async () => {
    await page.getByLabel('Yöntem').selectOption('HYBRID');
    await page.getByLabel('LLM sağlayıcı').selectOption('GROQ');
    await page.getByLabel('Model', { exact: true }).fill('llama-3.3-70b-versatile');
    await page.getByRole('button', { name: 'Analiz başlat' }).click();
    await page.waitForURL(/\/analyses\/\d+\/summary$/, { timeout: 15000 });
    state.runId = Number(page.url().split('/').slice(-2)[0]);
    await page.getByRole('region', { name: 'Analiz özeti' }).getByText('Kuyrukta').first().waitFor();
    await shot(page, '12-gercek-analysisrun');
    const db = probe('run', state.runId);
    expect(db.exists && db.owner === A.username && db.status === 'QUEUED' && db.snapshot_codes.length === 2, JSON.stringify(db));
    await page.goto(`${FRONT}/analyses`);
    await page.getByRole('link', { name: `#${state.runId}` }).waitFor();
    await page.goto(`${FRONT}/analyses/${state.runId}/endpoints`);
    await page.getByText('Kaynak kod analizi sonuçları henüz bağlı değil').waitFor();
    return db;
  });
  await step('E2E-17-18', 'Çıkış yapılır; refresh kara listeye alınır; korumalı sayfa ve geri tuşu önceki veriyi göstermez', async () => {
    state.lastRefresh = await page.evaluate(() => window.sessionStorage.getItem('testkalkan.refresh'));
    await page.getByRole('button', { name: /Kullanıcı menüsü/ }).click();
    // Refresh token'ın sunucuda kara listeye alındığı (205) açıkça beklenir.
    const blacklisted = page.waitForResponse((r) => r.url().endsWith('/api/auth/logout/') && r.status() === 205, { timeout: 15000 });
    await page.getByRole('menuitem', { name: /Çıkış yap/ }).click();
    await page.waitForURL(/\/login$/);
    await blacklisted;
    await page.goBack();
    await page.waitForTimeout(600);
    expect(/\/login$/.test(page.url()), `geri tuşu: ${page.url()}`);
    expect(!(await page.getByText(projectName).count()), 'çıkıştan sonra proje adı görünmemeli');
    await page.goto(`${FRONT}/projects/${state.projectId}`);
    await page.waitForURL(/\/login$/);
    // Kara listeye alınan refresh token artık kullanılamaz (sunucu doğrulaması).
    const reuse = await fetch(`${API}/api/auth/refresh/`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ refresh: state.lastRefresh || 'yok' }) });
    expect(state.lastRefresh && reuse.status === 401, `kara listedeki refresh yeniden kullanılabildi: ${reuse.status}`);
    return { logout_status: 205, blacklisted_refresh_reuse_status: reuse.status };
  });
  await step('E2E-19-22', 'Kullanıcı B, A\'nın kayıtlarını göremez; doğrudan URL backend tarafından reddedilir', async () => {
    await login(page, B);
    await page.waitForURL(/\/dashboard$/);
    state.bProjectId = await uploadProject(page, `B Projesi ${runTag}`);
    await page.goto(`${FRONT}/projects`);
    await page.getByRole('link', { name: `B Projesi ${runTag}` }).waitFor();
    expect(!(await page.getByText(projectName).count()), 'B listesinde A projesi görünmemeli');
    const statuses = [];
    page.on('response', (r) => {
      if (new URL(r.url()).pathname.match(/\/api\/(projects|analysis-runs)\/\d+\/$/)) statuses.push(r.status());
    });
    await page.goto(`${FRONT}/projects/${state.projectId}`);
    await page.getByText('Proje bulunamadı').waitFor();
    await shot(page, '15-yetkisiz-erisim-engeli');
    await page.goto(`${FRONT}/analyses/${state.runId}/summary`);
    await page.getByText('Analiz bulunamadı').waitFor();
    expect(statuses.length >= 2 && statuses.every((s) => s === 404), `durumlar: ${statuses}`);
    return { backend_statuses: statuses };
  });
  await step('E2E-23-25', 'A tekrar girer; aktif analizli silme 409; analiz sonlanınca silinir (CASCADE)', async () => {
    await page.getByRole('button', { name: /Kullanıcı menüsü/ }).click();
    await page.getByRole('menuitem', { name: /Çıkış yap/ }).click();
    await login(page, A);
    await page.waitForURL(/\/dashboard$/);
    expect(!(await page.getByText(`B Projesi ${runTag}`).count()), 'A, B verisini görmemeli (önbellek)');
    await page.goto(`${FRONT}/projects/${state.projectId}`);
    await page.getByRole('button', { name: 'Projeyi sil' }).click();
    await page.getByRole('dialog').getByRole('button', { name: 'Sil' }).click();
    await page.getByRole('dialog').getByText(/devam eden bir analizi var/).waitFor();
    await page.getByRole('dialog').screenshot({ path: path.join(SHOTS, '11-proje-silme-onayi.png') });
    expect(probe('project', state.projectId).exists, '409 sonrası proje silinmemeli');
    await page.getByRole('dialog').getByRole('button', { name: 'Vazgeç' }).click();
    probe('finish-run', state.runId);
    await page.getByRole('button', { name: 'Projeyi sil' }).click();
    await page.getByRole('dialog').getByRole('button', { name: 'Sil' }).click();
    await page.waitForURL(/\/projects$/);
    await page.getByRole('heading', { name: 'Projeler', exact: true }).waitFor();
    await page.getByRole('table').or(page.getByText('Henüz proje yok')).first().waitFor();
    expect(!(await page.getByRole('link', { name: projectName }).count()), 'silinen proje listede olmamalı');
    const db = probe('project', state.projectId);
    const run = probe('run', state.runId);
    expect(!db.exists && !run.exists, `db=${JSON.stringify(db)} run=${JSON.stringify(run)}`);
    return { project_exists: db.exists, run_exists: run.exists };
  });

  // ---- Access token süresi dolumu ve yenileme ----
  await step('AUTH-1', 'Access token süresi dolunca refresh ile yenilenir ve istek tamamlanır', async () => {
    const minutes = Number(BACKEND_ENV.JWT_ACCESS_MINUTES || 15);
    expect(minutes === 1, 'Bu senaryo JWT_ACCESS_MINUTES=1 ile çalışır');
    await page.goto(`${FRONT}/projects`);
    await page.getByRole('heading', { name: 'Projeler' }).waitFor();
    await page.waitForTimeout(62_000);
    const seen = [];
    const listener = (r) => {
      const p = new URL(r.url()).pathname;
      if (p.startsWith('/api/')) seen.push(`${r.request().method()} ${p} ${r.status()}`);
    };
    page.on('response', listener);
    await nav(page, '/analyses');
    await page.getByRole('heading', { name: 'Analizler' }).waitFor();
    await page.waitForTimeout(800);
    page.off('response', listener);
    const refreshOk = seen.filter((s) => s.startsWith('POST /api/auth/refresh/ 200')).length;
    expect(seen.some((s) => / 401$/.test(s)) && refreshOk === 1, seen.join(' | '));
    expect(seen.some((s) => s.startsWith('GET /api/analysis-runs/ 200')), seen.join(' | '));
    return { sequence: seen };
  });
  await step('AUTH-2', 'Sayfa yenilemede oturum korunur (refresh token ile)', async () => {
    await page.reload();
    await page.getByRole('heading', { name: 'Analizler' }).waitFor({ timeout: 10000 });
  });
  await step('AUTH-3', 'Refresh token sunucuda iptal edilirse oturum güvenli biçimde sonlanır', async () => {
    probe('blacklist-refresh', A.username);
    await page.reload();
    await page.waitForURL(/\/session-expired$/, { timeout: 10000 });
    const stored = await page.evaluate(() => window.sessionStorage.getItem('testkalkan.refresh'));
    expect(stored === null, 'refresh token temizlenmeli');
  });

  // ---- Hesap kilidi ----
  const lockPage = await newPage(browser);
  await step('LOCK-1', '1. ve 2. hatalı giriş 401 (kilit yok)', async () => {
    await login(lockPage, C, 'yanlis-parola-1');
    await lockPage.getByText('Kullanıcı adı veya parola hatalı.').waitFor();
    await shot(lockPage, '02-basarisiz-giris');
    await lockPage.getByLabel('Parola').fill('yanlis-parola-2');
    await lockPage.getByRole('button', { name: 'Giriş yap' }).click();
    await lockPage.waitForTimeout(600);
    expect(!(await lockPage.getByText('Hesap kilitlendi').count()), '2. denemede kilit olmamalı');
    expect(probe('axes-state', C.username).failures === 2, 'axes 2 başarısızlık saymalı');
  });
  await step('LOCK-2', '3. hatalı giriş 15 dakikalık kilidi başlatır; kalan süre sunucudan gösterilir', async () => {
    await lockPage.getByLabel('Parola').fill('yanlis-parola-3');
    await lockPage.getByRole('button', { name: 'Giriş yap' }).click();
    await lockPage.getByText('Hesap kilitlendi').waitFor();
    const remaining = await lockPage.getByTestId('lock-remaining').innerText();
    expect(/1[45] dk/.test(remaining), remaining);
    await shot(lockPage, '03-hesap-kilidi');
    const axes = probe('axes-state', C.username);
    expect(axes.locked_until, 'axes kilit zamanı olmalı');
    return { remaining, locked_until: axes.locked_until };
  });
  await step('LOCK-3', 'Kilit süresinde doğru parola reddedilir; sayfa yenilemede ve istemci saati ileri alınsa da kilit sürer', async () => {
    await lockPage.getByLabel('Parola').fill(C.password);
    await lockPage.getByRole('button', { name: 'Giriş yap' }).click();
    await lockPage.getByText('Hesap kilitlendi').waitFor();
    await lockPage.reload();
    await lockPage.clock.install({ time: Date.now() + 60 * 60 * 1000 }); // tarayıcı saati +1 saat
    await login(lockPage, C);
    await lockPage.getByText('Hesap kilitlendi').waitFor();
    expect(!/dashboard/.test(lockPage.url()), 'kilitliyken giriş olmamalı');
  });
  await step('LOCK-4', 'Kilit süresi dolunca (sunucu zamanı) doğru parolayla giriş yapılır ve sayaç sıfırlanır', async () => {
    await lockPage.close();
    probe('axes-expire', C.username);
    const p2 = await newPage(browser);
    await login(p2, C);
    await p2.waitForURL(/\/dashboard$/, { timeout: 10000 });
    expect(probe('axes-state', C.username).failures === 0, 'başarılı giriş sayacı sıfırlamalı');
    await p2.close();
  });

  // ---- Şifre sıfırlama (gerçek SMTP yakalayıcı) ----
  const resetPage = await newPage(browser);
  const newPassword = `E2e-Yeni-${Math.random().toString(36).slice(2, 10)}A1`;
  await step('RESET-1', 'Şifremi unuttum talebi gönderilir; genel yanıt gösterilir', async () => {
    state.mailFrom = Date.now() - 1000;
    await resetPage.goto(`${FRONT}/forgot-password`);
    await resetPage.getByLabel('E-posta').fill(A.email);
    await resetPage.getByRole('button', { name: 'Bağlantı gönder' }).click();
    await resetPage.getByText(/kayıtlıysa şifre sıfırlama bağlantısı gönderildi/).waitFor();
    await shot(resetPage, '04-sifremi-unuttum');
  });
  await step('RESET-2', 'Backend e-postayı SMTP ile gönderir; bağlantı frontend /reset-password rotasını gösterir', async () => {
    let mail = null;
    for (let i = 0; i < 20 && !mail; i += 1) {
      mail = latestMail(state.mailFrom);
      if (!mail) await new Promise((r) => setTimeout(r, 500));
    }
    expect(mail, 'SMTP yakalayıcıya e-posta ulaşmadı');
    // Quoted-printable yumuşak satır sonları yalnızca gövdede birleştirilir (başlıklar korunur).
    const split = mail.search(/\r?\n\r?\n/);
    const body = mail.slice(0, split) + mail.slice(split).replace(/=\r?\n/g, '');
    const match = body.match(/https?:\/\/[^\s]+\/reset-password\?uid=([^&\s]+)&token=([^\s]+)/);
    expect(match, 'e-postada sıfırlama bağlantısı yok');
    state.resetLink = match[0];
    const redacted = body
      .replace(/uid=[^&\s]+/g, 'uid=<redakte>')
      .replace(/token=[^\s]+/g, 'token=<redakte>')
      .replace(/^(To|From|Message-ID):.*$/gim, (line) => line.split(':')[0] + ': <redakte>');
    fs.writeFileSync(path.join(EVIDENCE, 'sifre-sifirlama-eposta.redakte.txt'), redacted.split('\n').filter((l) => !/^(Date|X-Peer|X-MailFrom|X-RcptTo):/i.test(l)).join('\n'));
    return { smtp: 'aiosmtpd 127.0.0.1:1025', route: new URL(state.resetLink).pathname };
  });
  await step('RESET-3', 'Bağlantı açılır, token adres çubuğundan silinir; yeni parola belirlenir', async () => {
    await resetPage.goto(state.resetLink);
    await resetPage.getByLabel(/^Yeni parola/).waitFor();
    expect(!/token=/.test(resetPage.url()), `adres hâlâ token içeriyor: ${new URL(resetPage.url()).pathname}`);
    await resetPage.getByLabel(/^Yeni parola/).fill('123');
    await resetPage.getByLabel(/Parola \(tekrar\)/).fill('123');
    await resetPage.getByRole('button', { name: 'Parolayı güncelle' }).click();
    await resetPage.locator('p.text-error').first().waitFor();
    await resetPage.getByLabel(/^Yeni parola/).fill(newPassword);
    await resetPage.getByLabel(/Parola \(tekrar\)/).fill(newPassword);
    await shot(resetPage, '05-yeni-parola-formu');
    await resetPage.getByRole('button', { name: 'Parolayı güncelle' }).click();
    await resetPage.waitForURL(/\/login$/);
    await resetPage.getByText('Parolanız güncellendi').waitFor();
    await shot(resetPage, '06-yeni-parola-basarili');
  });
  await step('RESET-4', 'Eski parola reddedilir (401), yeni parola ile giriş yapılır', async () => {
    await resetPage.getByLabel('Kullanıcı adı').fill(A.username);
    await resetPage.getByLabel('Parola').fill(A.password);
    await resetPage.getByRole('button', { name: 'Giriş yap' }).click();
    await resetPage.getByText('Kullanıcı adı veya parola hatalı.').waitFor();
    await login(resetPage, A, newPassword);
    await resetPage.waitForURL(/\/dashboard$/);
    A.password = newPassword;
    fs.writeFileSync(process.env.E2E_CREDS, JSON.stringify(CREDS), { mode: 0o600 });
  });
  await step('RESET-5', 'Kullanılmış ve geçersiz bağlantılar reddedilir', async () => {
    const p = await newPage(browser);
    await p.goto(state.resetLink);
    await p.getByLabel(/^Yeni parola/).fill(`${newPassword}x`);
    await p.getByLabel(/Parola \(tekrar\)/).fill(`${newPassword}x`);
    await p.getByRole('button', { name: 'Parolayı güncelle' }).click();
    await p.getByText(/geçersiz veya süresi dolmuş/).waitFor();
    await p.goto(`${FRONT}/reset-password?uid=MQ&token=gecersiz-token`);
    await p.getByLabel(/^Yeni parola/).fill('Baska-Parola-123');
    await p.getByLabel(/Parola \(tekrar\)/).fill('Baska-Parola-123');
    await p.getByRole('button', { name: 'Parolayı güncelle' }).click();
    await p.getByText(/geçersiz veya süresi dolmuş/).waitFor();
    await p.close();
  });

  // ---- Bağlantı kesintisi ve yeniden başlatma ----
  await step('NET-1', 'Backend durunca kullanıcıya bağlantı hatası gösterilir (sahte başarı yok)', async () => {
    await stopBackend();
    await waitForBackend(false);
    await resetPage.goto(`${FRONT}/projects/${state.bProjectId}`);
    // Bağlantı yokken saklanan oturum doğrulanamaz; kullanıcı girişe yönlenir ve giriş denemesi ağ hatası verir.
    await resetPage.waitForURL(/\/login$/, { timeout: 15000 });
    await resetPage.getByLabel('Kullanıcı adı').fill(A.username);
    await resetPage.getByLabel('Parola').fill(A.password);
    await resetPage.getByRole('button', { name: 'Giriş yap' }).click();
    await resetPage.getByText(/Sunucuya bağlanılamadı/).waitFor({ timeout: 15000 });
    await shot(resetPage, '17-baglanti-hatasi');
  });
  await step('NET-2', 'Backend yeniden başlatılınca oturum ve PostgreSQL kayıtları korunur', async () => {
    startBackend();
    await waitForBackend(true);
    await resetPage.reload();
    // Saklanan oturum doğrulanır; kullanıcı girişe takılmadan uygulamaya döner.
    await resetPage.waitForURL((url) => !/\/(login|session-expired)$/.test(url.pathname), { timeout: 15000 });
    await resetPage.getByRole('button', { name: /Kullanıcı menüsü/ }).waitFor();
    const b = probe('project', state.bProjectId);
    expect(b.exists && b.owner === B.username, JSON.stringify(b));
    return b;
  });

  // ---- Duyarlı tasarım ve konsol ----
  await step('RESP-1', '1440/1280/1024/768/390 px: yatay taşma yok', async () => {
    const pages = ['/dashboard', '/projects', '/projects/new', '/analyses', '/profile'];
    const problems = [];
    for (const width of [1440, 1280, 1024, 768, 390]) {
      const p = await newPage(browser, { width, height: 900 });
      await login(p, A);
      await p.waitForURL(/\/dashboard$/);
      for (const to of pages) {
        await nav(p, to);
        const overflow = await p.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
        if (overflow > 0) problems.push(`${width}px ${to}: ${overflow}px`);
      }
      if (width === 390) {
        await uploadProject(p, `Mobil ${runTag}`);
        await shot(p, '16-mobil-proje-detay');
        state.mobileProjectId = Number(p.url().split('/').pop());
      }
      for (const to of ['/login', '/forgot-password', '/reset-password?uid=MQ&token=x']) {
        const anon = await newPage(browser, { width, height: 900 });
        await anon.goto(`${FRONT}${to}`);
        await anon.waitForTimeout(300);
        const overflow = await anon.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
        if (overflow > 0) problems.push(`${width}px ${to}: ${overflow}px`);
        await anon.context().close();
      }
      await p.context().close();
    }
    expect(problems.length === 0, problems.join(', '));
  });

  // ---- Temizlik: test verisi kaldırılır ----
  await step('CLEAN', 'E2E test projeleri API ile silinir', async () => {
    if (state.projectId && probe('project', state.projectId).exists) {
      if (state.runId && probe('run', state.runId).exists) probe('finish-run', state.runId);
    }
    for (const [user, id] of [[B, state.bProjectId], [A, state.mobileProjectId], [A, state.projectId]]) {
      if (id && !probe('project', id).exists) continue;
      if (!id) continue;
      const tokens = await (await fetch(`${API}/api/auth/login/`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ username: user.username, password: user.password }) })).json();
      const res = await fetch(`${API}/api/projects/${id}/`, { method: 'DELETE', headers: { authorization: `Bearer ${tokens.access}` } });
      expect(res.status === 204, `silme ${id}: ${res.status}`);
    }
  });

  await browser.close();
  await stopBackend();

  const relevantConsole = consoleIssues.filter(
    (m) =>
      !/Failed to load resource: the server responded with a status of (400|401|403|404|409|429)/.test(m) &&
      !/net::ERR_CONNECTION_REFUSED/.test(m),
  );
  const summary = {
    generated_at: new Date().toISOString(),
    environment: { frontend: FRONT, api: API, database: 'PostgreSQL (gerçek)', smtp: 'yerel aiosmtpd yakalayıcı', browser: 'Chromium (Playwright)' },
    passed: results.filter((r) => r.status === 'PASS').length,
    failed: results.filter((r) => r.status === 'FAIL').length,
    results,
    console_issues: relevantConsole,
    expected_http_error_console_lines: consoleIssues.length - relevantConsole.length,
  };
  fs.writeFileSync(path.join(EVIDENCE, 'e2e-sonuclari.json'), `${JSON.stringify(summary, null, 2)}\n`);
  fs.writeFileSync(
    path.join(EVIDENCE, 'api-ornekleri.json'),
    `${JSON.stringify(apiExamples.map(({ key: _k, ...e }) => e).sort((a, b) => a.endpoint.localeCompare(b.endpoint) || a.method.localeCompare(b.method) || a.status - b.status), null, 2)}\n`,
  );
  log(`\nSONUÇ: ${summary.passed} PASS / ${summary.failed} FAIL; konsol sorunları: ${relevantConsole.length}`);
  process.exit(summary.failed === 0 && relevantConsole.length === 0 ? 0 : 1);
})().catch(async (error) => {
  log(`BEKLENMEYEN HATA: ${error.stack || error}`);
  await stopBackend();
  process.exit(2);
});
