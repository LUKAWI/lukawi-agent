const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();

  // Load the test page
  const testPath = path.join(__dirname, 'gfm-test.html');
  await page.goto('file:///' + testPath.replace(/\\/g, '/'));
  await page.waitForTimeout(3000);

  // Take screenshot
  await page.screenshot({
    path: path.join(__dirname, 'gfm-test-result.png'),
    fullPage: true
  });

  // Also test the actual app - inject test content
  try {
    await page.goto('http://localhost:5173');
    await page.waitForTimeout(2000);

    // Find the input area and type test content
    const input = await page.$('textarea');
    if (input) {
      const testContent = fs.readFileSync(path.join(__dirname, 'gfm-test-content.md'), 'utf8');
      await input.fill(testContent);
      await page.waitForTimeout(500);

      // Submit (press Enter)
      await input.press('Enter');
      await page.waitForTimeout(5000);

      // Take screenshot
      await page.screenshot({
        path: path.join(__dirname, 'app-gfm-test.png'),
        fullPage: true
      });
    }
  } catch (e) {
    console.log('Could not test app:', e.message);
  }

  await browser.close();
  console.log('Screenshots saved!');
})();
