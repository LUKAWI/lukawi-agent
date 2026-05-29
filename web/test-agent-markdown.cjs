const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const GFM_TEST_CONTENT = `请用markdown渲染以下内容测试：

# H1 Heading
## H2 Heading
### H3 Heading
#### H4 Heading
##### H5 Heading
###### H6 Heading

Auto-detected link: http://www.france.com

A line of normal text with \`inline code\` and *italics*, **strong font**, and even some μ†ℱ ╋ℯ╳╋.

Thin horizontal rule:

---

| Table Header 1 | Table Header 2 |
|----------------|----------------|
| Content | [http://example.org](http://example.org) |
| Content | Cell 2 |

> here is blockquote

\`\`\`ruby
class Classy
  def this_is
    puts "some #{colored} ruby code"
    @someobj.do_it(1, 2)
  end
end
\`\`\`

\`\`\`javascript
var test = function this_is(){
  console.log("javascript code with syntax highlighting");
}
\`\`\`

\`\`\`python
def hello():
    print("Hello, world!")
\`\`\`

Inline math: $E = mc^2$

Block math:
$$
\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}
$$

Task List:
- [x] Task 1 completed
- [ ] Task 2 pending
- [x] Task 3 completed

~~This text is struck through~~`;

(async () => {
  console.log('=== GFM Markdown Rendering Test ===\n');

  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

  // Navigate to the app
  console.log('1. Navigating to http://localhost:5173...');
  await page.goto('http://localhost:5173');
  await page.waitForTimeout(2000);

  // Check app loaded
  const title = await page.title();
  console.log(`   App title: ${title}`);

  // Find input area
  const input = await page.$('textarea');
  if (!input) {
    console.error('   ❌ Input area not found!');
    await browser.close();
    return;
  }
  console.log('   ✅ Input area found');

  // Type the test content
  console.log('2. Typing GFM test content...');
  await input.fill(GFM_TEST_CONTENT);
  await page.waitForTimeout(500);

  // Take screenshot before sending
  await page.screenshot({
    path: path.join(__dirname, 'test-before-send.png'),
    fullPage: false
  });
  console.log('   Screenshot saved: test-before-send.png');

  // Submit the message
  console.log('3. Submitting message...');
  await input.press('Enter');

  // Wait for response
  console.log('4. Waiting for agent response...');
  await page.waitForTimeout(8000);

  // Take screenshot after response
  await page.screenshot({
    path: path.join(__dirname, 'test-after-send.png'),
    fullPage: false
  });
  console.log('   Screenshot saved: test-after-send.png');

  // Check for markdown rendering
  console.log('\n5. Checking rendered elements...');
  
  const checks = await page.evaluate(() => {
    const results = {};
    results.markdownBody = document.querySelectorAll('.markdown-body').length;
    results.headings = {
      h1: document.querySelectorAll('.markdown-body h1').length,
      h2: document.querySelectorAll('.markdown-body h2').length,
      h3: document.querySelectorAll('.markdown-body h3').length,
    };
    results.tables = document.querySelectorAll('.markdown-body table').length;
    results.codeBlocks = document.querySelectorAll('.markdown-body pre').length;
    results.blockquotes = document.querySelectorAll('.markdown-body blockquote').length;
    results.links = document.querySelectorAll('.markdown-body a').length;
    results.inlineCode = document.querySelectorAll('.markdown-body code:not(pre code)').length;
    results.strong = document.querySelectorAll('.markdown-body strong').length;
    results.em = document.querySelectorAll('.markdown-body em').length;
    results.katex = document.querySelectorAll('.katex').length;
    results.del = document.querySelectorAll('.markdown-body del').length;
    results.checkboxes = document.querySelectorAll('.markdown-body input[type="checkbox"]').length;
    results.hr = document.querySelectorAll('.markdown-body hr').length;
    return results;
  });

  console.log('   Markdown body:', checks.markdownBody > 0 ? '✅' : '❌', `(${checks.markdownBody})`);
  console.log('   H1:', checks.headings.h1 > 0 ? '✅' : '❌', `(${checks.headings.h1})`);
  console.log('   H2:', checks.headings.h2 > 0 ? '✅' : '❌', `(${checks.headings.h2})`);
  console.log('   H3:', checks.headings.h3 > 0 ? '✅' : '❌', `(${checks.headings.h3})`);
  console.log('   Tables:', checks.tables > 0 ? '✅' : '❌', `(${checks.tables})`);
  console.log('   Code blocks:', checks.codeBlocks > 0 ? '✅' : '❌', `(${checks.codeBlocks})`);
  console.log('   Blockquotes:', checks.blockquotes > 0 ? '✅' : '❌', `(${checks.blockquotes})`);
  console.log('   Links:', checks.links > 0 ? '✅' : '❌', `(${checks.links})`);
  console.log('   Inline code:', checks.inlineCode > 0 ? '✅' : '❌', `(${checks.inlineCode})`);
  console.log('   Bold:', checks.strong > 0 ? '✅' : '❌', `(${checks.strong})`);
  console.log('   Italic:', checks.em > 0 ? '✅' : '❌', `(${checks.em})`);
  console.log('   KaTeX math:', checks.katex > 0 ? '✅' : '❌', `(${checks.katex})`);
  console.log('   Strikethrough:', checks.del > 0 ? '✅' : '❌', `(${checks.del})`);
  console.log('   Checkboxes:', checks.checkboxes > 0 ? '✅' : '❌', `(${checks.checkboxes})`);
  console.log('   Horizontal rule:', checks.hr > 0 ? '✅' : '❌', `(${checks.hr})`);

  // Take full page screenshot
  await page.screenshot({
    path: path.join(__dirname, 'test-full-page.png'),
    fullPage: true
  });
  console.log('\n   Full page screenshot saved: test-full-page.png');

  await browser.close();
  console.log('\n=== Test Complete ===');
})();
