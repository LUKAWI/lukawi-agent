const { chromium } = require('/home/admin/lukawi-agent/web/node_modules/playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });

  const page = await browser.newPage();
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: '/tmp/lukawi-desktop-v2.png', fullPage: false });
  console.log('Desktop saved');

  const dark = await browser.newPage();
  await dark.setViewportSize({ width: 1920, height: 1080 });
  await dark.goto('http://localhost:3000', { waitUntil: 'networkidle' });
  await dark.waitForTimeout(500);
  await dark.evaluate(() => { document.documentElement.dataset.theme = 'dark'; });
  await dark.waitForTimeout(500);
  await dark.screenshot({ path: '/tmp/lukawi-dark-v2.png', fullPage: false });
  console.log('Dark saved');

  const side = await browser.newPage();
  await side.setViewportSize({ width: 1920, height: 1080 });
  await side.goto('http://localhost:3000', { waitUntil: 'networkidle' });
  await side.waitForTimeout(500);
  const btn = await side.$('button[aria-label="Toggle sidebar"]');
  if (btn) await btn.click();
  await side.waitForTimeout(500);
  await side.screenshot({ path: '/tmp/lukawi-sidebar-v2.png', fullPage: false });
  console.log('Sidebar saved');

  await browser.close();
  console.log('Done');
})();
