const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  
  // Log console messages for debugging
  page.on('console', msg => {
    console.log(`[${msg.type()}] ${msg.text()}`);
  });
  page.on('pageerror', err => {
    console.log(`[PAGE ERROR] ${err.message}`);
  });

  // Navigate to the app
  console.log('1. Loading app...');
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  console.log('   Title:', await page.title());

  // Check if markdown-body class is present
  const hasMdBody = await page.$('.markdown-body');
  console.log('   markdown-body class:', hasMdBody ? '✅' : '❌ (expected empty state)');

  // Inject test content directly into the page to test processMarkdown
  console.log('\n2. Testing processMarkdown directly via page evaluation...');
  const mdTest = `$E = mc^2$ and $$\\int_0^\\infty e^{-x} dx = 1$$`;
  
  // Evaluate the imported function from the app's runtime
  const result = await page.evaluate((md) => {
    try {
      // Try to find processMarkdown in the window/module scope
      // The app's modules are bundled, so we can't access them directly
      // Instead, let's try to dynamically import the module via Vite's HMR
      return { error: 'Cannot access bundled modules directly' };
    } catch (e) {
      return { error: e.message };
    }
  }, mdTest);
  
  console.log('   Direct eval result:', result);

  // Alternative: inject markdown into a hidden div and check if KaTeX loads
  console.log('\n3. Checking if KaTeX and highlight.js are loaded from CDN...');
  const katexExists = await page.evaluate(() => typeof window.katex !== 'undefined');
  const hljsExists = await page.evaluate(() => typeof window.hljs !== 'undefined');
  console.log('   KaTeX client-side:', katexExists ? '✅' : '❌');
  console.log('   hljs client-side:', hljsExists ? '✅' : '❌');

  // Check what's rendered
  console.log('\n4. Page content snapshot...');
  const content = await page.evaluate(() => {
    const root = document.getElementById('root');
    return root ? root.innerHTML.substring(0, 500) : 'no root';
  });
  console.log('   Root content:', content);
  
  await browser.close();
  console.log('\nDone!');
})();
