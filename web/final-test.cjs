const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  
  // Load the actual app
  await page.goto('http://localhost:5173');
  await page.waitForTimeout(2000);

  // Inject test markdown content into the page to test rendering
  const testContent = `# H1 Heading
## H2 Heading
### H3 Heading

Auto-detected link: http://www.france.com

A line with \`inline code\` and *italics*, **strong font**.

---

| Table Header 1 | Table Header 2 |
|----------------|----------------|
| Cell 1 | Cell 2 |

\`\`\`javascript
var test = function() {
  console.log("hello");
}
\`\`\`

> here is blockquote

Inline math: $E = mc^2$

Block math:
$$
\\\\int_0^\\\\infty e^{-x^2} dx = \\\\frac{\\\\sqrt{\\\\pi}}{2}
$$

- [x] Task 1
- [ ] Task 2

~~Strikethrough text~~`;

  // Inject the markdown into the page using the app's own renderer
  const result = await page.evaluate(async (md) => {
    // Find the processMarkdown function in the app's modules
    // We'll test by directly calling it
    const response = await fetch('/src/lib/markdown.ts');
    return { status: response.status, ok: response.ok };
  }, testContent);

  console.log('Module fetch test:', result);

  // Take screenshot
  await page.screenshot({ path: path.join(__dirname, 'app-final.png'), fullPage: false });
  console.log('App screenshot saved');

  await browser.close();
})();
