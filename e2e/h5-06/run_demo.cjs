// H5-06 / #44 — Canlı demo akışının gerçek ortamda prova edilmesi ve ekran görüntüleri.
// Gerçek Chromium + Vite frontend + Django/DRF backend + PostgreSQL. API taklit EDİLMEZ.
// Sıra: giriş → dashboard → proje yükleme → liste/detay → referans JSON (5 metot) → analiz kaydı →
// deney sonuçları (çevrimdışı H5-05) → DEMO ekranlarının etiketleri → mobil görünüm → çıkış → temizlik.
// Çalıştırma: bash e2e/h5-06/run.sh (bkz. docs/demo/h5-06/README.md).
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
const SHOTS = process.env.DEMO_SHOTS || path.join(ROOT, 'docs/demo/h5-06/screenshots');
const EVIDENCE = process.env.DEMO_EVIDENCE || path.join(ROOT, 'docs/demo/h5-06');
const REFERENCE = path.join(ROOT, 'demo/h5_06/demo_data/referans_bes_metot.json');
const PROBE = path.join(ROOT, 'e2e/h5-03/db_probe.py');
const BACKEND_ENV = { ...process.env, ...JSON.parse(process.env.E2E_BACKEND_ENV || '{}') };
const SNAPSHOT = JSON.parse(fs.readFileSync(path.join(ROOT, 'frontend/src/data/h5-05-experiment.json'), 'utf8'));

fs.mkdirSync(SHOTS, { recursive: true });
const results = [];
const consoleIssues = [];
let backend = null;

const log = (m) => process.stdout.write(`${m}\n`);
const expect = (c, m) => {
  if (!c) throw new Error(m);
};

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

function probe(...args) {
  const out = execFileSync('python', [PROBE, ...args.map(String)], { cwd: BACKEND, env: BACKEND_ENV, encoding: 'utf8' });
  return JSON.parse(out.trim().split('\n').pop());
}

async function waitForBackend() {
  for (let i = 0; i < 60; i += 1) {
    try {
      if ((await fetch(`${API}/api/auth/me/`)).status === 401) return;
    } catch {
      /* henüz açılmadı */
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error('backend başlamadı');
}

async function newPage(browser, viewport = { width: 1440, height: 900 }) {
  const context = await browser.newContext({ viewport, deviceScaleFactor: 1 });
  const page = await context.newPage();
  page.on('console', (m) => {
    if (m.type() === 'error' || m.type() === 'warning') consoleIssues.push(`${m.type()}: ${m.text()}`);
  });
  page.on('pageerror', (e) => consoleIssues.push(`pageerror: ${e.message}`));
  return page;
}

async function shot(page, name, options = {}) {
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(SHOTS, `${name}.png`), fullPage: true, ...options });
}

async function overflow(page) {
  return page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
}

(async () => {
  const tag = Date.now().toString(36);
  const A = CREDS.A;
  const state = {};
  backend = spawn('python', ['manage.py', 'runserver', '127.0.0.1:8000', '--noreload'], {
    cwd: BACKEND,
    env: BACKEND_ENV,
    stdio: ['ignore', 'ignore', 'pipe'],
  });
  backend.stderr.on('data', () => {});
  await waitForBackend();
  const browser = await chromium.launch();
  const page = await newPage(browser);

  await step('D-00', 'Ön kontrol: backend PostgreSQL ile çalışıyor; frontend erişilebilir', async () => {
    const info = probe('backend');
    expect(info.vendor === 'postgresql', `vendor=${info.vendor}`);
    expect((await fetch(`${FRONT}/login`)).ok, 'frontend erişilemiyor');
    return info;
  });

  await step('D-01', 'Giriş ekranı → gerçek JWT girişi → dashboard', async () => {
    await page.goto(`${FRONT}/login`);
    await page.getByLabel('Kullanıcı adı').waitFor();
    await shot(page, '01-giris');
    await page.getByLabel('Kullanıcı adı').fill(A.username);
    await page.getByLabel('Parola').fill(A.password);
    await page.getByRole('button', { name: 'Giriş yap' }).click();
    await page.waitForURL(/\/dashboard$/, { timeout: 15000 });
    await page.getByRole('region', { name: 'Metrikler' }).waitFor();
    await shot(page, '02-dashboard');
  });

  const projectName = `Demo Sipariş API ${tag}`;
  await step('D-02', 'Proje yükleme (güvenli örnek ZIP, multipart) → PostgreSQL kaydı', async () => {
    await page.goto(`${FRONT}/projects/new`);
    await page.getByLabel('Proje adı').fill(projectName);
    await page.getByLabel('Açıklama (isteğe bağlı)').fill('Canlı demo örnek projesi (H5-06)');
    await page.getByLabel('Proje arşivi').setInputFiles(path.join(FIXTURES, 'ornek_api.zip'));
    await shot(page, '03-proje-yukleme');
    await page.getByRole('button', { name: 'Projeyi yükle' }).click();
    await page.waitForURL(/\/projects\/\d+$/, { timeout: 20000 });
    state.projectId = Number(page.url().split('/').pop());
    const db = probe('project', state.projectId);
    expect(db.exists && db.owner === A.username, JSON.stringify(db));
    return db;
  });

  await step('D-03', 'Proje listesi ve detay', async () => {
    await page.goto(`${FRONT}/projects`);
    await page.getByRole('link', { name: projectName }).waitFor();
    await shot(page, '04-proje-listesi');
    await page.getByRole('link', { name: projectName }).click();
    await page.getByRole('heading', { name: projectName }).waitFor();
    await shot(page, '05-proje-detay');
  });

  await step('D-04', 'Referans JSON: GET, POST, PUT, PATCH, DELETE gereksinimleri doğrulanıp kaydedilir', async () => {
    await page.getByRole('button', { name: 'JSON yükle' }).click();
    await page.locator('input[type=file][accept*=json]').setInputFiles(REFERENCE);
    await page.getByRole('button', { name: 'Doğrula ve kaydet' }).click();
    await page.getByRole('button', { name: 'DEMO-SIP-PATCH' }).waitFor({ timeout: 10000 });
    await page.reload();
    await page.getByRole('button', { name: 'DEMO-SIP-DELETE' }).waitFor({ timeout: 10000 });
    const db = probe('requirements', state.projectId);
    const methods = db.items.map((i) => i.method).sort();
    expect(JSON.stringify(methods) === JSON.stringify(['DELETE', 'GET', 'PATCH', 'POST', 'PUT']), JSON.stringify(methods));
    await page.getByRole('region', { name: 'Referans gereksinimler' }).screenshot({ path: path.join(SHOTS, '06-referans-json-5-metot.png') });
    return { methods };
  });

  await step('D-05', 'Gerçek AnalysisRun kaydı oluşturulur (QUEUED); sonuç servisleri "bağlı değil" olarak gösterilir', async () => {
    await page.getByLabel('Yöntem').selectOption('HYBRID');
    await page.getByLabel('LLM sağlayıcı').selectOption('GROQ');
    await page.getByLabel('Model', { exact: true }).fill('openai/gpt-oss-120b');
    await page.getByRole('button', { name: 'Analiz başlat' }).click();
    await page.waitForURL(/\/analyses\/\d+\/summary$/, { timeout: 15000 });
    state.runId = Number(page.url().split('/').slice(-2)[0]);
    await page.getByRole('region', { name: 'Analiz özeti' }).getByText('Kuyrukta').first().waitFor();
    await shot(page, '07-analiz-kaydi');
    const db = probe('run', state.runId);
    expect(db.exists && db.status === 'QUEUED' && db.snapshot_codes.length === 5, JSON.stringify(db));
    await page.goto(`${FRONT}/analyses/${state.runId}/tests`);
    await page.getByText(/henüz bağlı değil/).first().waitFor();
    await shot(page, '08-gercek-analiz-sonuc-servisi-bagli-degil');
    return db;
  });

  await step('D-06', 'Deney sonuçları: H5-05 çevrimdışı karşılaştırma tablosu (gerçek ölçümler, Ölçülemedi korunur)', async () => {
    await page.goto(`${FRONT}/experiments`);
    await page.getByRole('heading', { name: 'Deney sonuçları' }).waitFor();
    await page.getByText('ÇEVRİMDIŞI DENEY').waitFor();
    await page.getByText(SNAPSHOT.model).first().waitFor();
    expect((await page.getByRole('table').count()) === 2, 'iki katman tablosu beklenir');
    expect((await page.getByTestId('not-measurable').count()) === 3, 'Katman A F1 için 3 "Ölçülemedi" beklenir');
    const b = SNAPSHOT.layers.find((l) => l.key === 'B');
    const fpe = b.methods[1].firstPassExecutable;
    await page.getByText(`${fpe.count}/${fpe.of}`, { exact: false }).first().waitFor();
    await shot(page, '09-deney-sonuclari');
    return { sha: SNAPSHOT.sourceSha256.slice(0, 12) };
  });

  await step('D-07', 'DEMO/prototip ekranları açıkça etiketli (örnek analiz, canlı ilerleme, rapor)', async () => {
    await page.goto(`${FRONT}/demo/analyses`);
    await page.getByText('DEMO').first().waitFor();
    await shot(page, '10-demo-analiz-listesi');
    const first = page.locator('table a').first();
    await first.click();
    await page.waitForURL(/\/demo\/analyses\/[^/]+\/endpoints$/);
    await page.getByText(/Örnek veri: gerçek bir analiz/).waitFor();
    await shot(page, '11-demo-analiz-detay');
    await page.goto(page.url().replace(/\/endpoints$/, '/report'));
    await page.getByText(/DEMO/).first().waitFor();
    await shot(page, '12-demo-rapor');
  });

  await step('D-08', 'Mobil ve tablet görünümleri: deney sonuçları ve proje ekranlarında yatay taşma yok', async () => {
    const problems = [];
    for (const width of [390, 768, 1024, 1440]) {
      const p = await newPage(browser, { width, height: 900 });
      await p.goto(`${FRONT}/login`);
      await p.getByLabel('Kullanıcı adı').fill(A.username);
      await p.getByLabel('Parola').fill(A.password);
      await p.getByRole('button', { name: 'Giriş yap' }).click();
      await p.waitForURL(/\/dashboard$/);
      for (const to of ['/experiments', '/projects', `/projects/${state.projectId}`, '/dashboard']) {
        await p.goto(`${FRONT}${to}`);
        await p.waitForTimeout(500);
        const o = await overflow(p);
        if (o > 0) {
          const culprit = await p.evaluate(() => {
            const vw = document.documentElement.clientWidth;
            const els = [...document.querySelectorAll('body *')].filter((e) => {
              const r = e.getBoundingClientRect();
              return r.right > vw + 1 && !e.closest('.overflow-x-auto');
            });
            const e = els[els.length - 1];
            return e ? `${e.tagName.toLowerCase()}.${String(e.className).slice(0, 60)} "${(e.textContent || '').slice(0, 40)}"` : '?';
          });
          problems.push(`${width}px ${to}: ${o}px (${culprit})`);
        }
      }
      if (width === 390) {
        await p.goto(`${FRONT}/experiments`);
        await p.getByRole('heading', { name: 'Deney sonuçları' }).waitFor();
        await shot(p, '13-mobil-deney-sonuclari');
      }
      await p.context().close();
    }
    expect(problems.length === 0, problems.join(', '));
  });

  await step('D-09', 'Çıkış: oturum kapanır, korumalı sayfa girişe yönlendirir', async () => {
    await page.goto(`${FRONT}/dashboard`);
    await page.getByRole('button', { name: /Kullanıcı menüsü/ }).click();
    await page.getByRole('menuitem', { name: /Çıkış yap/ }).click();
    await page.waitForURL(/\/login$/);
    await page.goto(`${FRONT}/experiments`);
    await page.waitForURL(/\/login$/);
  });

  await step('D-CLEAN', 'Demo verisi temizlenir (analiz kaydı sonlandırılır, proje API ile silinir)', async () => {
    if (state.runId && probe('run', state.runId).exists) probe('finish-run', state.runId);
    if (state.projectId && probe('project', state.projectId).exists) {
      const tokens = await (
        await fetch(`${API}/api/auth/login/`, {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ username: A.username, password: A.password }),
        })
      ).json();
      const res = await fetch(`${API}/api/projects/${state.projectId}/`, {
        method: 'DELETE',
        headers: { authorization: `Bearer ${tokens.access}` },
      });
      expect(res.status === 204, `silme: ${res.status}`);
    }
  });

  await browser.close();
  backend.kill('SIGTERM');
  const relevant = consoleIssues.filter(
    (m) => !/Failed to load resource: the server responded with a status of (400|401|403|404|409)/.test(m),
  );
  const summary = {
    generated_at: new Date().toISOString(),
    environment: { frontend: FRONT, api: API, database: 'PostgreSQL (gerçek)', browser: 'Chromium (Playwright)' },
    experiment_snapshot_sha256: SNAPSHOT.sourceSha256,
    passed: results.filter((r) => r.status === 'PASS').length,
    failed: results.filter((r) => r.status === 'FAIL').length,
    results,
    console_issues: relevant,
  };
  fs.writeFileSync(path.join(EVIDENCE, 'demo-provasi-sonuclari.json'), `${JSON.stringify(summary, null, 2)}\n`);
  log(`\nSONUÇ: ${summary.passed} PASS / ${summary.failed} FAIL; konsol sorunları: ${relevant.length}`);
  process.exit(summary.failed === 0 && relevant.length === 0 ? 0 : 1);
})().catch((error) => {
  log(`BEKLENMEYEN HATA: ${error.stack || error}`);
  if (backend) backend.kill('SIGTERM');
  process.exit(2);
});
