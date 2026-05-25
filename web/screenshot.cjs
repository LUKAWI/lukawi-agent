const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();

  // Desktop 1920x1080 - Welcome screen
  const desktop = await browser.newPage();
  await desktop.setViewportSize({ width: 1920, height: 1080 });
  await desktop.goto('http://localhost:3000', { waitUntil: 'networkidle' });
  await desktop.waitForTimeout(1000);
  await desktop.screenshot({ path: '/tmp/lukawi-desktop.png', fullPage: false });
  console.log('1/4 Desktop welcome saved');

  // Desktop with sidebar open
  const sidebar = await browser.newPage();
  await sidebar.setViewportSize({ width: 1920, height: 1080 });
  await sidebar.goto('http://localhost:3000', { waitUntil: 'networkidle' });
  await sidebar.waitForTimeout(500);
  const menuBtn = await sidebar.$('button[aria-label="Toggle sidebar"]');
  if (menuBtn) await menuBtn.click();
  await sidebar.waitForTimeout(500);
  await sidebar.screenshot({ path: '/tmp/lukawi-desktop-sidebar.png', fullPage: false });
  console.log('2/4 Desktop with sidebar saved');

  // Dark mode
  const darkPage = await browser.newPage();
  await darkPage.setViewportSize({ width: 1920, height: 1080 });
  await darkPage.goto('http://localhost:3000', { waitUntil: 'networkidle' });
  await darkPage.waitForTimeout(500);
  await darkPage.evaluate(() => { document.documentElement.dataset.theme = 'dark'; });
  await darkPage.waitForTimeout(500);
  await darkPage.screenshot({ path: '/tmp/lukawi-dark.png', fullPage: false });
  console.log('3/4 Dark mode saved');

  // Mobile 375x812
  const mobile = await browser.newPage();
  await mobile.setViewportSize({ width: 375, height: 812 });
  await mobile.goto('http://localhost:3000', { waitUntil: 'networkidle' });
  await mobile.waitForTimeout(500);
  await mobile.screenshot({ path: '/tmp/lukawi-mobile.png', fullPage: false });
  console.log('4/4 Mobile saved');

  await browser.close();
  console.log('All screenshots done');
})();
