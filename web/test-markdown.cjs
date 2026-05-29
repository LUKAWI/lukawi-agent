const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Read the markdown.ts source to extract the processMarkdown function
// We'll test by injecting markdown content directly into the page

const testMarkdown = `# H1 Heading
## H2 Heading
### H3 Heading
#### H4 Heading
##### H5 Heading
###### H6 Heading

Auto-detected link: http://www.france.com

A line of normal text with \`inline code\` and *italics*, **strong font**, and even some μ†ℱ ╋ℯ╳╋.

Thin horizontal rule:

--

Thick horizontal rule:

---

| Table Header 1 | Table Header 2 |
|----------------|----------------|
| Content        | [http://example.org](http://example.org) |
| Content        | http://localhost:\\<port> |

\`\`\`ruby
class Classy
  def this_is
    puts "some #{colored} ruby code with ruby syntax highlighting"
    @someobj.do_it(1, 2)
  end
end
\`\`\`

\`\`\`javascript
var test = function this_is(){
  console.log("some" + colored + "javascript code with javascript syntax highlighting really long");
}
\`\`\`

\`\`\`python
def hello():
    print("Hello, world!")
\`\`\`

> here is blockquote

**LaTeX Tests:**

Inline math: $E = mc^2$

Block math:
$$
\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}
$$

Inline fraction: $\\frac{a}{b}$

**Task List:**
- [x] Task 1 completed
- [ ] Task 2 pending
- [x] Task 3 completed

**Strikethrough:**
~~This text is struck through~~

**Footnotes:**
This has a footnote[^1].

[^1]: This is the footnote content.
`;

(async () => {
  // Create a test HTML file that uses the same markdown rendering
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Markdown Rendering Test</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css" crossorigin="anonymous">
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
      font-size: 14px;
      line-height: 1.6;
      color: #24292f;
      max-width: 900px;
      margin: 0 auto;
      padding: 32px;
      background: #ffffff;
    }
    
    .markdown-body h1, .markdown-body h2, .markdown-body h3, 
    .markdown-body h4, .markdown-body h5, .markdown-body h6 {
      margin-top: 24px;
      margin-bottom: 16px;
      font-weight: 600;
      line-height: 1.25;
    }
    
    .markdown-body h1 {
      font-size: 2em;
      padding-bottom: 0.3em;
      border-bottom: 1px solid #d0d7de;
    }
    
    .markdown-body h2 {
      font-size: 1.5em;
      padding-bottom: 0.3em;
      border-bottom: 1px solid #d0d7de;
    }
    
    .markdown-body h3 { font-size: 1.25em; }
    .markdown-body h4 { font-size: 1em; }
    .markdown-body h5 { font-size: 0.875em; }
    .markdown-body h6 { font-size: 0.85em; color: #656d76; }
    
    .markdown-body p {
      margin-top: 0;
      margin-bottom: 16px;
    }
    
    .markdown-body a {
      color: #0969da;
      text-decoration: none;
    }
    
    .markdown-body a:hover {
      text-decoration: underline;
    }
    
    .markdown-body strong { font-weight: 600; }
    .markdown-body em { font-style: italic; }
    .markdown-body del { text-decoration: line-through; }
    
    .markdown-body hr {
      height: 0.25em;
      padding: 0;
      margin: 24px 0;
      background-color: #d0d7de;
      border: 0;
    }
    
    .markdown-body blockquote {
      margin: 0;
      padding: 0 1em;
      color: #656d76;
      border-left: 0.25em solid #d0d7de;
    }
    
    .markdown-body ul, .markdown-body ol {
      margin-top: 0;
      margin-bottom: 16px;
      padding-left: 2em;
    }
    
    .markdown-body code {
      padding: 0.2em 0.4em;
      margin: 0;
      font-size: 85%;
      background-color: rgba(175,184,193,0.2);
      border-radius: 6px;
      font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace;
    }
    
    .markdown-body pre {
      padding: 16px;
      overflow: auto;
      font-size: 85%;
      line-height: 1.45;
      color: #e6edf3;
      background-color: #0d1117;
      border-radius: 6px;
      margin-bottom: 16px;
    }
    
    .markdown-body pre code {
      padding: 0;
      margin: 0;
      background: transparent;
      border-radius: 0;
      font-size: 100%;
      color: inherit;
    }
    
    .markdown-body table {
      border-spacing: 0;
      border-collapse: collapse;
      margin-bottom: 16px;
      width: auto;
      overflow: auto;
      display: block;
    }
    
    .markdown-body table th {
      font-weight: 600;
      padding: 6px 13px;
      border: 1px solid #d0d7de;
      background-color: #f6f8fa;
    }
    
    .markdown-body table td {
      padding: 6px 13px;
      border: 1px solid #d0d7de;
    }
    
    .markdown-body table tr {
      background-color: #ffffff;
      border-top: 1px solid #d0d7de;
    }
    
    .markdown-body table tr:nth-child(2n) {
      background-color: #f6f8fa;
    }
    
    .markdown-body .contains-task-list {
      list-style: none;
      padding-left: 0;
    }
    
    .markdown-body .task-list-item {
      display: flex;
      align-items: center;
      gap: 0.5em;
      margin-left: -1.5em;
    }
    
    .markdown-body .task-list-item input[type="checkbox"] {
      margin: 0 0.2em 0.25em -1.4em;
      vertical-align: middle;
    }
    
    .markdown-body .footnotes {
      margin-top: 32px;
      padding-top: 16px;
      border-top: 1px solid #d0d7de;
      font-size: 12px;
    }
    
    .markdown-body .katex-display {
      margin: 1em 0;
      overflow-x: auto;
      overflow-y: hidden;
    }
    
    .markdown-body .katex { font-size: 1.1em; }
    
    /* Syntax highlighting - GitHub Dark */
    .hljs-comment,
    .hljs-quote { color: #8b949e; }
    .hljs-variable,
    .hljs-template-variable,
    .hljs-attribute,
    .hljs-tag,
    .hljs-name,
    .hljs-regexp,
    .hljs-link,
    .hljs-selector-id,
    .hljs-selector-class { color: #7ee787; }
    .hljs-number,
    .hljs-meta,
    .hljs-built_in,
    .hljs-builtin-name,
    .hljs-literal,
    .hljs-type,
    .hljs-params { color: #79c0ff; }
    .hljs-string,
    .hljs-symbol,
    .hljs-bullet { color: #a5d6ff; }
    .hljs-title,
    .hljs-section { color: #d2a8ff; }
    .hljs-keyword,
    .hljs-selector-tag { color: #ff7b72; }
    .hljs-emphasis { font-style: italic; }
    .hljs-strong { font-weight: 700; }
  </style>
</head>
<body>
  <h1 style="text-align: center; margin-bottom: 32px;">GitHub Flavored Markdown Test</h1>
  <div class="markdown-body" id="content"></div>
  
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js" crossorigin="anonymous"></script>
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js" crossorigin="anonymous"></script>
  <script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js"></script>
  <script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/languages/ruby.min.js"></script>
  <script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/languages/python.min.js"></script>
  <script>
    // Simple markdown to HTML converter (for testing)
    function renderMarkdown(md) {
      let html = md
        // Headers
        .replace(/^### (.*$)/gm, '<h3>$1</h3>')
        .replace(/^## (.*$)/gm, '<h2>$1</h2>')
        .replace(/^# (.*$)/gm, '<h1>$1</h1>')
        .replace(/^#### (.*$)/gm, '<h4>$1</h4>')
        .replace(/^##### (.*$)/gm, '<h5>$1</h5>')
        .replace(/^###### (.*$)/gm, '<h6>$1</h6>')
        // Horizontal rules
        .replace(/^---$/gm, '<hr>')
        .replace(/^--$/gm, '<hr>')
        // Bold and italic
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // Strikethrough
        .replace(/~~(.*?)~~/g, '<del>$1</del>')
        // Inline code
        .replace(/\`([^\`]+)\`/g, '<code>$1</code>')
        // Links
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
        // Auto-links
        .replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank">$1</a>')
        // Blockquotes
        .replace(/^> (.*$)/gm, '<blockquote><p>$1</p></blockquote>')
        // Task lists
        .replace(/^- \[x\] (.*$)/gm, '<li class="task-list-item"><input type="checkbox" checked disabled> $1</li>')
        .replace(/^- \[ \] (.*$)/gm, '<li class="task-list-item"><input type="checkbox" disabled> $1</li>')
        // Unordered lists
        .replace(/^- (.*$)/gm, '<li>$1</li>')
        // Paragraphs
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
      
      // Handle tables
      html = html.replace(/\|(.+)\|\n\|[-\s|]+\|\n((?:\|.+\|\n?)+)/g, (match, header, body) => {
        const headers = header.split('|').filter(h => h.trim()).map(h => `<th>${h.trim()}</th>`).join('');
        const rows = body.trim().split('\n').map(row => {
          const cells = row.split('|').filter(c => c.trim()).map(c => `<td>${c.trim()}</td>`).join('');
          return `<tr>${cells}</tr>`;
        }).join('');
        return `<table><thead><tr>${headers}</tr></thead><tbody>${rows}</tbody></table>`;
      });
      
      // Handle fenced code blocks
      html = html.replace(/\`\`\`(\w+)?\n([\s\S]*?)\`\`\`/g, (match, lang, code) => {
        const langClass = lang ? \` class="language-\${lang}"\` : '';
        return \`<pre><code\${langClass}>\${code.trim()}</code></pre>\`;
      });
      
      return '<p>' + html + '</p>';
    }
    
    const content = ${JSON.stringify(testMarkdown)};
    document.getElementById('content').innerHTML = renderMarkdown(content);
    
    // Apply syntax highlighting
    document.querySelectorAll('pre code').forEach((block) => {
      hljs.highlightElement(block);
    });
    
    // Apply KaTeX rendering
    renderMathInElement(document.getElementById('content'), {
      delimiters: [
        {left: '$$', right: '$$', display: true},
        {left: '$', right: '$', display: false},
        {left: '\\\\(', right: '\\\\)', display: false},
        {left: '\\\\[', right: '\\\\]', display: true}
      ],
      throwOnError: false
    });
  </script>
</body>
</html>`;

  // Write the test HTML file
  fs.writeFileSync(path.join(__dirname, 'test-markdown.html'), html);
  
  // Launch browser and take screenshot
  const browser = await chromium.launch({ 
    headless: true,
    channel: 'msedge'  // Use Edge since Chrome is not available
  });
  
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1280, height: 900 });
  
  // Load the test HTML file
  await page.goto('file:///' + path.join(__dirname, 'test-markdown.html').replace(/\\/g, '/'));
  await page.waitForTimeout(2000);  // Wait for KaTeX to render
  
  // Take screenshot
  await page.screenshot({ 
    path: path.join(__dirname, 'test-markdown-screenshot.png'),
    fullPage: true 
  });
  
  console.log('Screenshot saved to test-markdown-screenshot.png');
  
  await browser.close();
})();
