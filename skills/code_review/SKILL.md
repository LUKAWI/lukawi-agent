---
name: code_review
description: Review code for bugs, security issues, and style problems
triggers:
  - review
  - code review
  - check my code
  - is this code
  - review this
---

# Code Review Skill

When asked to review code, follow this process:

1. **Security**: Check for injection, XSS, path traversal, hardcoded secrets
2. **Correctness**: Check for logic errors, off-by-one, race conditions
3. **Performance**: Check for N+1 queries, memory leaks, unnecessary allocation
4. **Style**: Check naming, consistency, error handling patterns

## Output Format

```
## Review: <file/brief description>

### Security Issues
- ...

### Correctness Issues
- ...

### Suggestions
- ...
```

## Important

Be constructive. Focus on the most impactful issues first.
