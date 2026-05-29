# DESIGN.md — Lukawi Agent WebUI Redesign

> A premium, dark-first AI developer workspace — where precision meets elegance.

## 1. Visual Theme & Atmosphere

**Style**: Dark Editorial × Minimal Tech — Linear meets Cursor meets Vercel
**Keywords**: deep, precise, luminous, editorial, glass, refined, focused, developer
**Tone**: Professional-grade developer tool — NOT playful, NOT cluttered, NOT heavy
**Feel**: A meticulously crafted dark workspace where information glows with purpose, like a premium code editor at night.

**Interaction Tier**: L2 (流畅交互) — smooth transitions, scroll reveals, hover micro-interactions
**Dependencies**: CSS only (no GSAP needed for chat app — use CSS transitions + React state)

---

## 2. Color Palette & Roles

```css
:root {
  /* ── Light Theme ── */
  --bg: #f8f9fb;                          /* Page background */
  --surface: #ffffff;                     /* Cards, panels, header */
  --surface-alt: #f1f3f6;                /* Alternating surfaces, hover states */
  --surface-hover: #eaecf1;              /* Button/Card hover */

  --border: #e2e5ea;                     /* Default borders */
  --border-hover: #c8ccd4;               /* Border on hover */

  --text: #111318;                       /* Primary text — headings */
  --text-secondary: #5a5f6b;             /* Secondary — descriptions */
  --text-tertiary: #8b909c;              /* Tertiary — labels, captions */

  --accent: #4f6ef6;                     /* Primary accent — CTA, links */
  --accent-hover: #3d5ce5;               /* Accent hover */
  --accent-muted: #e8ebfe;               /* Accent background tint */

  /* RGB for rgba() usage */
  --bg-rgb: 248, 249, 251;
  --accent-rgb: 79, 110, 246;

  /* Semantic */
  --success: #10b981;
  --success-muted: #d1fae5;
  --error: #ef4444;
  --error-muted: #fce4e4;
  --warning: #f59e0b;
  --warning-muted: #fef3c7;

  /* Shadows — Light */
  --shadow-xs: 0 1px 2px rgba(0,0,0,0.03);
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.03);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04);
  --shadow-lg: 0 12px 24px rgba(0,0,0,0.08), 0 4px 8px rgba(0,0,0,0.04);
  --shadow-glow: 0 0 0 1px rgba(79,110,246,0.1), 0 0 20px rgba(79,110,246,0.08);
}

[data-theme="dark"] {
  color-scheme: dark;

  --bg: #0a0b0f;                         /* Deepest background */
  --surface: #111318;                    /* Cards, panels */
  --surface-alt: #1a1d24;               /* Alternating, inputs */
  --surface-hover: #22252e;             /* Hover states */

  --border: #252830;                    /* Subtle borders */
  --border-hover: #363a44;              /* Borders on hover */

  --text: #e8eaed;                      /* Primary */
  --text-secondary: #8e939d;            /* Secondary */
  --text-tertiary: #5f636d;             /* Tertiary */

  --accent: #7185f7;                    /* Brighter for dark bg */
  --accent-hover: #8a9af9;              /* Accent hover */
  --accent-muted: rgba(113,133,247,0.1);/* Accent tint */

  --bg-rgb: 10, 11, 15;
  --accent-rgb: 113, 133, 247;

  --success: #34d399;
  --success-muted: rgba(52,211,153,0.1);
  --error: #f87171;
  --error-muted: rgba(248,113,113,0.1);
  --warning: #fbbf24;
  --warning-muted: rgba(251,191,36,0.1);

  /* Shadows — Dark */
  --shadow-xs: 0 1px 2px rgba(0,0,0,0.25);
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.35);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.4);
  --shadow-lg: 0 12px 24px rgba(0,0,0,0.5);
  --shadow-glow: 0 0 0 1px rgba(113,133,247,0.15), 0 0 24px rgba(113,133,247,0.1);
}
```

**Color Rules:**
- ALL colors via CSS variables — ZERO hardcoded hex/rgb in components
- Dark theme as default experience; light theme as respectful alternative
- Accent used sparingly — only on interactive elements and active states
- Glass effect (`backdrop-filter: blur()`) used on surface elements for depth

---

## 3. Typography Rules

**Font Stack:**
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', 'SF Mono', 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
```

| Role | Font | Size | Weight | Line Height | Letter Spacing |
|------|------|------|--------|-------------|----------------|
| App Title | Inter | 15px | 700 | 1 | -0.01em |
| Section Header | Inter | 11px | 700 | 1 | 0.06em |
| Message Body | Inter | 14px | 400 | 1.65 | 0 |
| Code Block | JetBrains Mono | 13px | 400 | 1.6 | 0 |
| Sidebar Label | Inter | 13px | 500 | 1.4 | 0 |
| Sidebar Meta | Inter | 11px | 500 | 1.3 | 0 |
| Input | Inter | 14px | 400 | 1.5 | 0 |
| Welcome Title | Inter | 32px | 800 | 1.2 | -0.02em |
| Welcome Desc | Inter | 15px | 400 | 1.6 | 0 |

**Typography Rules:**
- Heading weight ≥ 700 always
- Body never below 13px; code never below 12px
- Chinese text: line-height ≥ 1.7, letter-spacing: 0.02em
- **NEVER use**: serif fonts, Comic Sans, system-ui as only fallback without Inter

**Text Decoration:**
- Welcome title: Gradient text (accent → text-primary, 135deg) — signature brand moment
- Section headers: Uppercase, tracked-out, muted — structural only
- No text shadows, no outline text — keep it clean

---

## 4. Component Stylings

### 4.1 Buttons

```css
/* Primary — accent fill */
.btn-primary {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  padding: 8px 16px;
  border: none; border-radius: 8px;
  background: var(--accent); color: #fff;
  font-family: var(--font-sans); font-size: 13px; font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
}
.btn-primary:hover { background: var(--accent-hover); transform: translateY(-1px); box-shadow: var(--shadow-glow); }
.btn-primary:active { transform: translateY(0) scale(0.97); }
.btn-primary:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; transform: none; box-shadow: none; }

/* Secondary — ghost/outline */
.btn-ghost {
  display: inline-flex; align-items: center; justify-content: center;
  padding: 6px 10px;
  border: 1px solid transparent; border-radius: 6px;
  background: transparent; color: var(--text-secondary);
  font-family: var(--font-sans); font-size: 13px; font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-ghost:hover { background: var(--surface-hover); color: var(--text); border-color: var(--border); }
.btn-ghost:active { transform: scale(0.97); }
.btn-ghost:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

/* Icon-only button */
.btn-icon {
  display: flex; align-items: center; justify-content: center;
  width: 32px; height: 32px;
  border: none; border-radius: 6px;
  background: transparent; color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-icon:hover { background: var(--surface-hover); color: var(--text); }
.btn-icon:active { transform: scale(0.92); }
.btn-icon.active { background: var(--accent-muted); color: var(--accent); }
```

### 4.2 Sidebar

```css
/* Sidebar — glass panel on desktop, drawer on mobile */
.sidebar {
  width: 280px; height: 100%;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex; flex-direction: column;
  overflow: hidden;
  transition: width 0.3s cubic-bezier(0.4,0,0.2,1);
}
.sidebar.collapsed { width: 0; border-right: none; }

/* Section */
.sidebar-section {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
}
.sidebar-section-header {
  display: flex; align-items: center; gap: 6px;
  padding: 4px 6px 8px;
  margin-bottom: 4px;
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-tertiary);
  cursor: pointer; user-select: none;
  border-bottom: 1px solid var(--border);
}
.sidebar-section-header:hover { color: var(--text-secondary); }

/* Collapsible content — animated grid-rows */
.sidebar-collapsible {
  display: grid; grid-template-rows: 0fr;
  transition: grid-template-rows 0.3s cubic-bezier(0.4,0,0.2,1);
}
.sidebar-collapsible.open { grid-template-rows: 1fr; }
.sidebar-collapsible-inner { overflow: hidden; }

/* List item */
.sidebar-item {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 8px; margin: 1px 0;
  border-radius: 6px;
  font-size: 13px; font-weight: 500;
  color: var(--text);
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: all 0.15s ease;
}
.sidebar-item:hover { background: var(--surface-hover); }
.sidebar-item.active {
  background: var(--accent-muted);
  border-left-color: var(--accent);
  color: var(--accent);
}
```

### 4.3 Input Bar

```css
.input-bar {
  padding: 12px 20px 16px;
  border-top: 1px solid var(--border);
  background: var(--surface);
}
.input-row {
  display: flex; align-items: flex-end; gap: 8px;
  background: var(--surface-alt);
  border: 2px solid var(--border);
  border-radius: 14px;
  padding: 6px 6px 6px 16px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.input-row:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.12);
}
.chat-input {
  flex: 1; min-height: 24px; max-height: 200px;
  padding: 6px 0;
  border: none; background: transparent;
  color: var(--text);
  font-family: var(--font-sans); font-size: 14px; line-height: 1.5;
  outline: none; resize: none;
}
.chat-input::placeholder { color: var(--text-tertiary); }
.chat-input:disabled { opacity: 0.4; cursor: not-allowed; }
.send-btn {
  display: flex; align-items: center; justify-content: center;
  width: 36px; height: 36px; flex-shrink: 0;
  border: none; border-radius: 10px;
  background: var(--accent); color: #ffffff;
  cursor: pointer;
  transition: all 0.15s ease;
}
.send-btn:hover:not(:disabled) { background: var(--accent-hover); transform: scale(1.05); }
.send-btn:active:not(:disabled) { transform: scale(0.92); }
.send-btn:disabled { opacity: 0.3; cursor: not-allowed; transform: none; }
```

### 4.4 Message Bubbles

```css
.message {
  animation: msgIn 0.35s cubic-bezier(0.16,1,0.3,1);
}
@keyframes msgIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
.message-user {
  max-width: 85%; margin-left: auto;
  background: var(--accent); color: #ffffff;
  border-radius: 16px 16px 4px 16px;
  padding: 10px 16px;
}
.message-assistant {
  max-width: 85%;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 14px 18px;
  box-shadow: var(--shadow-xs);
}
```

### 4.5 Tags / Badges

```css
.badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px; font-weight: 600; letter-spacing: 0.02em;
  background: var(--surface-alt); color: var(--text-secondary);
  border: 1px solid var(--border);
}
.badge.active { background: var(--accent-muted); color: var(--accent); border-color: transparent; }
.badge.success { background: var(--success-muted); color: var(--success); }
.badge.error { background: var(--error-muted); color: var(--error); }
```

---

## 5. Layout Principles

**Container:**
- App is full-height (100vh), flex column layout
- Main content: flex row (sidebar + chat panel)
- Sidebar: 280px fixed width, collapsible to 0
- Chat panel: flex 1, fills remaining space

**Spacing Scale:**
- Component padding: 12px–20px
- Message gap: 16px
- Section gap: 8px
- Card internal padding: 12px–16px

**Grid:**
```css
.app-layout {
  display: flex; flex-direction: column; height: 100vh;
}
.app-main {
  display: flex; flex: 1; min-height: 0; overflow: hidden;
}
```

---

## 6. Depth & Elevation

| Level | Treatment | Use |
|-------|-----------|-----|
| Flat | No shadow, bg color only | Page background |
| Subtle | `shadow-xs` (0 1px 2px) | Cards, message bubbles |
| Elevated | `shadow-sm` (0 1px 3px) | Sidebar (desktop), header |
| Modal | `shadow-lg` (0 12px 24px) | Dialogs, dropdowns |
| Glow | `shadow-glow` (accent glow) | Active/focused inputs |

---

## 7. Animation & Interaction

**Motion Philosophy**: Subtle, purposeful, fast. Use only opacity, transform, and border-color. No movement heavier than 12px translation.

**Tier**: L2 — Scroll reveal, hover effects, enter/exit transitions

### 7.1 Entrance
```css
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-in {
  animation: fadeInUp 0.4s cubic-bezier(0.16,1,0.3,1) both;
}
```

### 7.2 Message Appearance
```css
.message-enter {
  animation: msgIn 0.35s cubic-bezier(0.16,1,0.3,1) both;
}
@keyframes msgIn {
  from { opacity: 0; transform: translateY(12px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
```

### 7.3 Sidebar Toggle
```css
.sidebar-transition {
  transition: width 0.3s cubic-bezier(0.4,0,0.2,1),
              opacity 0.3s cubic-bezier(0.4,0,0.2,1);
}
```

### 7.4 Hover States (ALL interactive elements)
```css
.interactive {
  transition: background 0.15s ease, color 0.15s ease,
              border-color 0.15s ease, transform 0.15s ease,
              box-shadow 0.15s ease;
}
.interactive:hover { transform: translateY(-1px); }
.interactive:active { transform: translateY(0) scale(0.97); }
```

### 7.5 Loading States
```css
/* Streaming cursor blink */
.cursor-blink {
  animation: blink 1s step-end infinite;
}
@keyframes blink {
  50% { opacity: 0; }
}

/* Spinner */
.spinner {
  width: 16px; height: 16px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
```

### 7.6 Welcome Screen
```css
.welcome-enter {
  animation: welcomeIn 0.6s cubic-bezier(0.16,1,0.3,1) both;
}
@keyframes welcomeIn {
  from { opacity: 0; transform: translateY(24px); }
  to { opacity: 1; transform: translateY(0); }
}
.welcome-title {
  background: linear-gradient(135deg, var(--text) 30%, var(--accent) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

### 7.7 Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 8. Do's and Don'ts

### Do
- Use CSS variables for ALL colors — zero hardcoded values
- Keep interactive target size ≥ 44×44px on mobile
- Show focus ring on :focus-visible for keyboard navigation
- Use backdrop-filter glass effects on dark theme surfaces for depth
- Animate only opacity and transform for 60fps
- Provide clear visual feedback on all interactive states (hover, active, focus, disabled)
- Use border-left accent indicator for active items
- Keep message bubbles clean with generous padding

### Don't
- ❌ Hardcode any hex/rgb color values in component CSS
- ❌ Use `filter: blur()` on animated elements (GPU expensive)
- ❌ Animate elements larger than 200px in height
- ❌ Use serif fonts anywhere in the app
- ❌ Have empty hover states — every interactive element needs hover feedback
- ❌ Use box-shadow heavier than shadow-lg for non-modal elements
- ❌ Allow horizontal overflow on mobile (< 600px)
- ❌ Use `display: none` for hiding — use opacity/transform transitions instead
- ❌ Add more than 2 simultaneous animations per viewport
- ❌ Skip focus-visible styles for any interactive element
- ❌ Use pure black (#000) or pure white (#fff) — always use variables

---

## 9. Responsive Behavior

**Breakpoints:**
| Name | Width | Key Changes |
|------|-------|-------------|
| Desktop | > 768px | Full sidebar (280px), two-column layout |
| Mobile | ≤ 768px | Sidebar as overlay drawer, single column, header + chat fill viewport |

**Touch Targets:** minimum 44×44px
**Collapsing Strategy:**
- Desktop: Sidebar toggles between 280px and 0px (Ctrl+B)
- Mobile: Sidebar slides in from left as overlay with backdrop blur

```css
/* Desktop */
@media (min-width: 769px) {
  .sidebar { width: 280px; }
  .sidebar.collapsed { width: 0; overflow: hidden; }
}

/* Mobile */
@media (max-width: 768px) {
  .sidebar {
    position: fixed; left: 0; top: 48px; bottom: 0;
    z-index: 50; width: 280px;
    transform: translateX(-100%); opacity: 0;
    transition: transform 0.3s ease, opacity 0.3s ease;
    box-shadow: var(--shadow-lg);
  }
  .sidebar.open { transform: translateX(0); opacity: 1; }
  .sidebar-backdrop {
    position: fixed; inset: 0; z-index: 40;
    background: rgba(0,0,0,0.4);
    backdrop-filter: blur(2px);
  }
  .input-bar { padding: 8px 12px 12px; }
  .message { max-width: 95%; }
}
```

---

## Implementation Notes

1. **Keep existing API layer** (`api.js`) — no changes needed
2. **Keep existing state management** (`AppContext.jsx`) — reducer pattern is clean
3. **Keep existing SSE hook** (`useSSE.js`) — streaming logic unchanged
4. **Rewrite all CSS** — single design system, no legacy carryover
5. **Rewrite all components** — new markup, new class names, new animations
6. **Build output target**: `../src/lukawi/server/static/` (from vite.config.js)
7. **Icons**: Use lucide-react for consistency, or keep existing SVG icons

---

> Motion effects inspired by reactbits by DavidHDev (MIT)
> Design philosophy: "Information glows with purpose in the dark"
