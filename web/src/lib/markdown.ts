import { unified, type Plugin } from 'unified';
import remarkParse from 'remark-parse';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import remarkRehype from 'remark-rehype';
import rehypeKatex from 'rehype-katex';
import rehypeHighlight from 'rehype-highlight';
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize';
import rehypeStringify from 'rehype-stringify';

// Custom link renderer to open links in new tab
const customLinkRenderer: Plugin = () => {
  return (tree) => {
    const visit = (node: any) => {
      if (node.tagName === 'a' && node.properties?.href) {
        node.properties.target = '_blank';
        node.properties.rel = 'noopener noreferrer';
      }
      if (node.children) {
        node.children.forEach(visit);
      }
    };
    visit(tree);
  };
};

// Create the markdown processor
// Pipeline order: parse → transform → SANITIZE → render math → stringify
// rehypeSanitize MUST run BEFORE rehypeKatex so that KaTeX's complex HTML output
// (inline styles, dozens of internal classes, aria-hidden, etc.) is never stripped.
const processor = unified()
  .use(remarkParse)
  .use(remarkGfm, {
    singleTilde: false, // GitHub uses ~~ for strikethrough
  })
  .use(remarkMath)
  .use(remarkRehype)
  .use(rehypeHighlight, {
    ignoreMissing: true,
  })
  .use(rehypeSanitize, {
    ...defaultSchema,
    attributes: {
      ...defaultSchema.attributes,
      // Allow remark-math's intermediate wrapper classes (math-inline / math-display)
      // so rehypeKatex can find and replace them in the next step.
      span: [
        ...(defaultSchema.attributes?.span || []),
        ['className', /^(math|hljs)/],
      ],
      div: [
        ...(defaultSchema.attributes?.div || []),
        ['className', /^math/],
      ],
      // Allow syntax highlighting language classes
      code: [
        ...(defaultSchema.attributes?.code || []),
        ['className', /^(language-|hljs)/],
      ],
      pre: [
        ...(defaultSchema.attributes?.pre || []),
        ['className', /^(language-|hljs)/],
      ],
      // Allow footnote attributes
      a: [
        ...(defaultSchema.attributes?.a || []),
        ['data-footnote-ref'],
        ['data-footnote-backref'],
      ],
      // Allow task list checkboxes
      input: [
        ...(defaultSchema.attributes?.input || []),
        ['type', 'checkbox'],
        ['disabled'],
        ['checked'],
      ],
    },
  })
  .use(rehypeKatex, {
    throwOnError: false,
    errorColor: '#cc0000',
    output: 'htmlAndMathml',
    trust: false,
    strict: 'warn',
    macros: {
      '\\R': '\\mathbb{R}',
      '\\N': '\\mathbb{N}',
      '\\Z': '\\mathbb{Z}',
      '\\C': '\\mathbb{C}',
    },
    maxSize: 10,
    maxExpand: 1000,
    globalGroup: false,
  })
  .use(customLinkRenderer)
  .use(rehypeStringify);

/**
 * Process markdown content to HTML
 * Supports GFM, LaTeX math, and syntax highlighting
 */
export function processMarkdown(content: string): string {
  try {
    const result = processor.processSync(content);
    return String(result);
  } catch (error) {
    console.error('Markdown processing error:', error);
    // Fallback to basic HTML escaping
    return content
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}

/**
 * Check if content contains LaTeX math expressions
 */
export function hasMathContent(content: string): boolean {
  return content.includes('$') || content.includes('\\(') || content.includes('\\[');
}

/**
 * Check if content contains code blocks
 */
export function hasCodeBlocks(content: string): boolean {
  return content.includes('```') || content.includes('~~~');
}