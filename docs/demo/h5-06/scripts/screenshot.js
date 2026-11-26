// H5-06 ekran görüntüsü yakalama (Playwright) — koyu tema, canlı frontend+backend.
// Kullanım (Playwright ayrı kurulur; frontend/package.json'a dokunmamak için):
//   mkdir shots && cd shots && npm init -y && npm i playwright && npx playwright install chromium
//   node <bu dosya>              (backend 8000 + frontend 5173 ayakta, demo kullanıcıları tohumlu iken)
// Çıktı: docs/demo/h5-06/ekran-goruntuleri/*.png
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE = process.env.FRONTEND_BASE || 'http://localhost:5173';
const PW = process.env.DEMO_PW || 'DemoParola!2026';
const USER = process.env.DEMO_USER || 'demo_merve';
const PROJECT_ID = process.env.DEMO_PROJECT_ID || '1';
const OUT = path.resolve(__dirname, '..', 'ekran-goruntuleri');

fs.mkdirSync(OUT, { recursive: true });

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
  await ctx.addInitScript(() => { try { localStorage.setItem('theme', 'dark'); } catch (e) {} });
  const page = await ctx.newPage();

  const shot = async (name) => {
    try { await page.waitForTimeout(700); await page.screenshot({ path: path.join(OUT, name), fullPage: true }); console.log('OK  ' + name); }
    catch (e) { console.log('XX  ' + name + ' :: ' + e.message); }
  };
  const go = async (p) => {
    try { await page.goto(BASE + p, { waitUntil: 'networkidle', timeout: 20000 }); }
    catch (e) { console.log('nav uyarı ' + p + ' :: ' + e.message); }
  };
  const login = async () => {
    await go('/login');
    try { await page.getByLabel('Kullanıcı adı').fill(USER); } catch { await page.locator('input').nth(0).fill(USER); }
    try { await page.getByLabel('Parola').fill(PW); } catch { await page.locator('input[type="password"]').first().fill(PW); }
    await page.getByRole('button', { name: /giriş|giris|oturum/i }).first().click();
    await page.waitForURL(/dashboard/, { timeout: 20000 });
  };

  // Herkese açık ekranlar
  await go('/login'); await shot('01-giris.png');
  await go('/forgot-password'); await shot('02-sifremi-unuttum.png');
  await go('/reset-password'); await shot('03-yeni-parola-belirleme.png');

  // Giriş sonrası (gerçek backend)
  try { await login(); } catch (e) { console.log('giriş uyarı :: ' + e.message); }
  await shot('04-dashboard.png');
  await go('/projects'); await shot('05-projeler-liste.png');
  await go('/projects/' + PROJECT_ID); await shot('06-proje-detay.png');
  await go('/projects/new'); await shot('07-proje-yukleme.png');
  await go('/profile'); await shot('08-profil.png');

  // DEMO analiz ekranları (prototip/DEMO veri)
  await go('/demo/analyses'); await shot('09-analizler-demo-liste.png');
  const link = page.locator('a[href*="/demo/analyses/"]').first();
  if (await link.count()) {
    await link.click(); await page.waitForLoadState('networkidle');
    const m = page.url().match(/demo\/analyses\/([^/?#]+)/);
    const id = m ? m[1] : null;
    await shot('10-analiz-endpointler-demo.png');
    if (id) for (const [t, n] of [['tests', '11-uretilen-testler-demo.png'], ['results', '12-test-sonuclari-demo.png'],
      ['findings', '13-guvenlik-bulgulari-demo.png'], ['report', '14-rapor-demo.png']]) { await go(`/demo/analyses/${id}/${t}`); await shot(n); }
  }

  await browser.close();
  console.log('Bitti -> ' + OUT);
})();
