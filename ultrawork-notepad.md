# Ultrawork Notepad — Markdown & LaTeX Rendering Optimization
Started: 2026-05-28

## Plan (exhaustive, atomic)
1. Explore codebase to understand current markdown/LaTeX implementation
2. Analyze github-flavored-markdown-test requirements
3. Benchmark current rendering against test suite
4. Identify gaps and missing features
5. Implement markdown improvements (GFM support)
6. Add LaTeX rendering support (KaTeX or MathJax)
7. Add syntax highlighting for code blocks
8. Test and verify against github-flavored-markdown-test
9. Manual QA with screenshots

## Scenarios (the contract)
### Scenario 1: Happy Path - Basic Markdown Rendering
- **Pass condition**: All basic markdown elements (headings, paragraphs, lists, links, images) render correctly
- **Real surface**: Browser screenshot showing proper rendering
- **Test file**: Manual testing with github-flavored-markdown-test README

### Scenario 2: Edge Case - Complex GFM Features
- **Pass condition**: Tables, task lists, strikethrough, autolinks render correctly
- **Real surface**: Browser screenshot showing GFM features
- **Test file**: github-flavored-markdown-test specific test cases

### Scenario 3: Adjacent-surface - LaTeX Math Rendering
- **Pass condition**: Inline and block math expressions render correctly
- **Real surface**: Browser screenshot showing math formulas
- **Test file**: Custom LaTeX test cases

## Now (single step in progress)
- Waiting for exploration agents to complete
- Gathering context about current implementation

## Todo (remaining, ordered)
1. Wait for explore/librarian agents to complete
2. Analyze current implementation gaps
3. Create detailed work plan
4. Implement markdown improvements
5. Add LaTeX support
6. Add syntax highlighting
7. Test and verify
8. Manual QA with screenshots

## Findings (non-obvious facts with file:line refs)
- Current implementation uses `marked` library (v18.0.3) for markdown parsing
- No LaTeX support currently exists
- No markdown-specific CSS styles found
- MessageList.tsx line 80-81: Uses `marked.parse` with `breaks: true` option
- No syntax highlighting for code blocks
- No `.markdown-body` CSS styles defined anywhere
- No XSS sanitization - raw HTML goes directly to dangerouslySetInnerHTML
- github-flavored-markdown-test is a visual reference, not programmatic test suite
- Test cases include: headings, inline formatting, links, horizontal rules, tables, code blocks with syntax highlighting, blockquotes, images, escaping

## Learnings (patterns / pitfalls for next turn)
- Project uses React with TypeScript
- Tailwind CSS for styling
- Vite as build tool
- Need to switch from `marked` to `unified` + `remark` ecosystem for better GFM support
- Use `remark-gfm` for tables, task lists, strikethrough, autolinks
- Use `remark-math` + `rehype-katex` for LaTeX support
- Use `rehype-highlight` for syntax highlighting
- Use `rehype-sanitize` for XSS protection
- KaTeX is faster than MathJax for most use cases
- Need to create `.markdown-body` CSS styles matching GitHub's styling