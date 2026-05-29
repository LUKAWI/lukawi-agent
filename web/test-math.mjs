import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import remarkRehype from 'remark-rehype';
import rehypeKatex from 'rehype-katex';
import rehypeHighlight from 'rehype-highlight';
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize';
import rehypeStringify from 'rehype-stringify';

const processor = unified()
  .use(remarkParse)
  .use(remarkGfm)
  .use(remarkMath)
  .use(remarkRehype)
  .use(rehypeHighlight, { ignoreMissing: true })
  .use(rehypeSanitize, {
    ...defaultSchema,
    attributes: {
      ...defaultSchema.attributes,
      span: [
        ...(defaultSchema.attributes?.span || []),
        ['className', /^(math|hljs)/],
      ],
      div: [
        ...(defaultSchema.attributes?.div || []),
        ['className', /^math/],
      ],
      code: [['className', /^(language-|hljs)/]],
      pre: [['className', /^(language-|hljs)/]],
    },
  })
  .use(rehypeKatex, { throwOnError: false })
  .use(rehypeStringify);

const tests = [
  'Inline math: $E = mc^2$',
  'Block math: $$\n\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}\n$$',
  'Just inline $x + y = z$ here',
  'Multiple: $a$ and $b$ and $c$',
  'Fraction: $\\frac{a}{b}$',
  'Greek: $\\alpha + \\beta = \\gamma$',
  'Sum: $\\sum_{i=1}^{n} i$',
  // Test with backslash escaped dollars
  'Escape: \\$not math\\$',
  // Edge: dollar at start
  '$x = 5$ is a value',
  // Edge: multi-paragraph
  'First para with $a^2 + b^2 = c^2$.\n\nSecond para with $$E = mc^2$$.',
];

for (const md of tests) {
  try {
    const result = processor.processSync(md);
    console.log('=== INPUT ===');
    console.log(md);
    console.log('=== OUTPUT ===');
    const html = String(result);
    const hasKatexClass = html.includes('class="katex"') || html.includes("class='katex'");
    const hasStrut = html.includes('strut');
    const hasMathContent = html.includes('mathnormal') || html.includes('mord') || html.includes('msup');
    const hasStyle = html.includes('style=');
    if (hasKatexClass && hasStrut && hasMathContent) {
      console.log('✓ KaTeX fully rendered (class + strut + math nodes + style)');
      console.log(html.substring(0, 500));
    } else if (hasKatexClass) {
      console.log('⚠ KaTeX class present but structure incomplete');
      console.log(`  strut=${hasStrut} mathContent=${hasMathContent} style=${hasStyle}`);
      console.log(html.substring(0, 500));
    } else {
      console.log('✗ NO KaTeX rendering!');
      console.log(html.substring(0, 500));
    }
    console.log('');
  } catch (e) {
    console.log('=== INPUT ===');
    console.log(md);
    console.log('=== ERROR ===');
    console.log(e.message);
    console.log('');
  }
}
