const pw = require('/home/admin/lukawi-agent/web/node_modules/playwright');

(async () => {
  const browser = await pw.chromium.launch({ headless: true });

  // Light desktop
  const light = await browser.newPage();
  await light.setViewportSize({ width: 1920, height: 1080 });
  await light.goto('http://localhost:3000', { waitUntil: 'networkidle' });
  await light.waitForTimeout(1000);
  await light.screenshot({ path: '/tmp/lukawi-v3-light.png', fullPage: false });

  // Dark desktop
  const dark = await browser.newPage();
  await dark.setViewportSize({ width: 1920, height: 1080 });
  await dark.goto('http://localhost:3000', { waitUntil: 'networkidle' });
  await dark.waitForTimeout(500);
  await dark.evaluate(() => { document.documentElement.dataset.theme = 'dark'; });
  await dark.waitForTimeout(500);
  await dark.screenshot({ path: '/tmp/lukawi-v3-dark.png', fullPage: false });

  await browser.close();
  console.log('Done');
})();
