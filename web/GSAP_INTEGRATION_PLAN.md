# GSAP Integration Plan for Lukawi WebUI

## Overview

This document outlines the detailed plan for integrating GSAP (GreenSock Animation Platform) into the Lukawi Agent WebUI to enhance user experience with professional-grade animations while maintaining performance and accessibility.

---

## 1. Installation & Setup

### 1.1 Dependencies

```bash
cd web
npm install gsap @gsap/react
```

### 1.2 Global Configuration

Create `src/lib/gsap.ts`:

```typescript
import { gsap } from "gsap";
import { useGSAP } from "@gsap/react";

// Register plugins
gsap.registerPlugin(useGSAP);

// Global defaults
gsap.defaults({
  duration: 0.4,
  ease: "power2.out",
});

// Respect reduced-motion preference
const mm = gsap.matchMedia();

mm.add(
  {
    reduceMotion: "(prefers-reduced-motion: reduce)",
    noPreference: "(prefers-reduced-motion: no-preference)",
  },
  (context) => {
    const { reduceMotion } = context.conditions;
    
    // Override defaults for reduced motion
    if (reduceMotion) {
      gsap.defaults({ duration: 0, ease: "none" });
    }
  }
);

export { gsap, useGSAP, mm };
```

### 1.3 Remove Conflicting CSS Animations

Update `tailwind.config.ts` to remove animations that will be replaced by GSAP:

```typescript
// Keep only utility animations (blink, pulse-dot)
// Remove message-in and fade-in (GSAP will handle these)
keyframes: {
  'blink': {
    '50%': { opacity: '0' },
  },
  'pulse-dot': {
    '0%, 100%': { opacity: '1' },
    '50%': { opacity: '0.4' },
  },
},
animation: {
  'blink': 'blink 1s step-end infinite',
  'pulse-dot': 'pulse-dot 1.5s ease-in-out infinite',
},
```

---

## 2. Component-by-Component Animation Plan

### 2.1 WelcomeScreen.tsx — First Impression

**Current:** Simple `fade-in` animation

**Enhanced Animation Sequence:**

```typescript
import { useRef } from "react";
import { useGSAP } from "@gsap/react";
import { gsap } from "gsap";

export default function WelcomeScreen() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { sendMessage } = useSSE();

  useGSAP(() => {
    const tl = gsap.timeline({ defaults: { ease: "power3.out" } });
    
    // Logo entrance — scale + rotate
    tl.from(".welcome-logo", {
      scale: 0,
      rotation: -180,
      duration: 0.8,
      ease: "back.out(1.7)",
    });
    
    // Title — slide up with fade
    tl.from(".welcome-title", {
      y: 30,
      opacity: 0,
      duration: 0.5,
    }, "-=0.3");
    
    // Description — fade in
    tl.from(".welcome-desc", {
      y: 20,
      opacity: 0,
      duration: 0.4,
    }, "-=0.2");
    
    // Example buttons — stagger entrance
    tl.from(".welcome-example", {
      y: 20,
      opacity: 0,
      scale: 0.9,
      stagger: 0.1,
      duration: 0.4,
      ease: "back.out(1.5)",
    }, "-=0.2");
    
    // Version badge — subtle fade
    tl.from(".welcome-version", {
      opacity: 0,
      duration: 0.3,
    }, "-=0.1");

  }, { scope: containerRef });

  return (
    <div ref={containerRef} className="flex-1 flex flex-col items-center justify-center px-6 py-8">
      {/* Add classes for GSAP targeting */}
      <Logo size={56} className="welcome-logo" />
      <h1 className="welcome-title ...">Lukawi Agent</h1>
      <p className="welcome-desc ...">...</p>
      <div className="welcome-example ...">...</div>
      <div className="welcome-version ...">v0.2.0</div>
    </div>
  );
}
```

**Animation Properties:**
- Duration: ~2s total sequence
- Easing: `power3.out` (smooth deceleration), `back.out` (subtle overshoot)
- Performance: All transforms (scale, rotation, y, opacity)

---

### 2.2 MessageList.tsx — Chat Message Animations

**Current:** CSS `animate-message-in` (opacity + translateY)

**Enhanced with GSAP:**

```typescript
import { useRef, useCallback } from "react";
import { useGSAP } from "@gsap/react";
import { gsap } from "gsap";

function MessageItem({ msg, isStreaming }: MessageItemProps) {
  const msgRef = useRef<HTMLDivElement>(null);
  
  // Entrance animation on mount
  useGSAP(() => {
    gsap.from(msgRef.current, {
      y: 20,
      opacity: 0,
      scale: 0.98,
      duration: 0.4,
      ease: "power2.out",
    });
  }, { scope: msgRef });

  return (
    <div ref={msgRef} className="card-message">
      {/* ... */}
    </div>
  );
}

// Stagger animation for initial message load
function MessageList() {
  const listRef = useRef<HTMLDivElement>(null);
  const { state } = useApp();
  const prevLengthRef = useRef(0);

  useGSAP(() => {
    const messages = listRef.current?.querySelectorAll(".card-message");
    if (!messages) return;
    
    // Only animate NEW messages (not re-renders)
    const newMessages = Array.from(messages).slice(prevLengthRef.current);
    if (newMessages.length === 0) return;
    
    gsap.from(newMessages, {
      y: 20,
      opacity: 0,
      scale: 0.98,
      stagger: 0.08,
      duration: 0.4,
      ease: "power2.out",
      clearProps: "all", // Clean up inline styles after animation
    });
    
    prevLengthRef.current = messages.length;
  }, { 
    dependencies: [state.messages.length],
    scope: listRef,
  });

  return (
    <div ref={listRef} className="flex-1 overflow-y-auto p-4 space-y-3">
      {/* ... */}
    </div>
  );
}
```

**Performance Considerations:**
- Use `clearProps: "all"` to remove inline styles after animation
- Only animate new messages, not re-renders
- Stagger: 0.08s between messages (smooth cascade)

---

### 2.3 ToolCard.tsx — Expand/Collapse Animation

**Current:** Instant show/hide with CSS

**Enhanced with smooth height animation:**

```typescript
function ToolCard({ toolCall }: { toolCall: ToolCallBlock }) {
  const [collapsed, setCollapsed] = useState(toolCall.collapsed !== false);
  const contentRef = useRef<HTMLDivElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  // Animate expand/collapse
  useGSAP(() => {
    if (!contentRef.current) return;
    
    if (collapsed) {
      gsap.to(contentRef.current, {
        height: 0,
        opacity: 0,
        duration: 0.3,
        ease: "power2.inOut",
        onComplete: () => {
          if (contentRef.current) {
            contentRef.current.style.display = "none";
          }
        },
      });
    } else {
      if (contentRef.current) {
        contentRef.current.style.display = "block";
      }
      gsap.fromTo(contentRef.current, 
        { height: 0, opacity: 0 },
        { 
          height: "auto", 
          opacity: 1, 
          duration: 0.3, 
          ease: "power2.inOut",
        }
      );
    }
  }, { dependencies: [collapsed], scope: cardRef });

  // Status icon animation
  useGSAP(() => {
    if (toolCall.status === "running") {
      gsap.to(".tool-status-icon", {
        rotation: 360,
        repeat: -1,
        duration: 1,
        ease: "none",
      });
    }
  }, { dependencies: [toolCall.status] });

  return (
    <div ref={cardRef} className="border ...">
      <button onClick={() => setCollapsed(!collapsed)}>
        {/* ... */}
      </button>
      <div ref={contentRef} className="px-3 pb-3 pt-2 border-t ...">
        {/* Content */}
      </div>
    </div>
  );
}
```

---

### 2.4 Sidebar.tsx — Panel Animation

**Current:** CSS `transition-all` for width/opacity

**Enhanced with GSAP:**

```typescript
export default function Sidebar() {
  const sidebarRef = useRef<HTMLElement>(null);
  const { state } = useApp();

  // Sidebar show/hide animation
  useGSAP(() => {
    if (!sidebarRef.current) return;
    
    if (state.sidebarVisible) {
      gsap.fromTo(sidebarRef.current,
        { width: 0, opacity: 0 },
        { 
          width: 260, 
          opacity: 1, 
          duration: 0.3, 
          ease: "power2.out",
        }
      );
    } else {
      gsap.to(sidebarRef.current, {
        width: 0,
        opacity: 0,
        duration: 0.25,
        ease: "power2.in",
      });
    }
  }, { dependencies: [state.sidebarVisible] });

  // Section expand/collapse (already has CSS, enhance with GSAP)
  function Section({ title, icon, defaultOpen, badge, children }: SectionProps) {
    const [open, setOpen] = useState(defaultOpen);
    const contentRef = useRef<HTMLDivElement>(null);
    const chevronRef = useRef<SVGSVGElement>(null);

    useGSAP(() => {
      // Chevron rotation
      gsap.to(chevronRef.current, {
        rotation: open ? 90 : 0,
        duration: 0.2,
        ease: "power2.out",
      });
      
      // Content height animation
      if (contentRef.current) {
        gsap.to(contentRef.current, {
          height: open ? "auto" : 0,
          duration: 0.25,
          ease: "power2.inOut",
        });
      }
    }, { dependencies: [open] });

    return (
      <div className="mb-1">
        <button onClick={() => setOpen(!open)}>
          <ChevronRight ref={chevronRef} size={12} />
          {/* ... */}
        </button>
        <div ref={contentRef} className="overflow-hidden">
          {children}
        </div>
      </div>
    );
  }

  return (
    <aside
      ref={sidebarRef}
      className="w-[260px] shrink-0 h-full flex flex-col bg-[var(--surface)] border-r ..."
    >
      {/* ... */}
    </aside>
  );
}
```

---

### 2.5 InputBar.tsx — Micro-interactions

**Enhanced button and input animations:**

```typescript
export default function InputBar() {
  const sendBtnRef = useRef<HTMLButtonElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Send button press animation
  const handleSendPress = useCallback(() => {
    if (!sendBtnRef.current) return;
    
    gsap.to(sendBtnRef.current, {
      scale: 0.85,
      duration: 0.1,
      ease: "power2.in",
      onComplete: () => {
        gsap.to(sendBtnRef.current, {
          scale: 1,
          duration: 0.3,
          ease: "elastic.out(1, 0.3)",
        });
      },
    });
  }, []);

  // Suggestions dropdown animation
  useGSAP(() => {
    if (!suggestionsRef.current) return;
    
    const items = suggestionsRef.current.querySelectorAll(".suggestion-item");
    gsap.from(items, {
      y: -10,
      opacity: 0,
      stagger: 0.05,
      duration: 0.2,
      ease: "power2.out",
    });
  }, { dependencies: [suggestions.length] });

  // Input focus glow animation
  useGSAP(() => {
    const inputContainer = inputRef.current?.parentElement;
    if (!inputContainer) return;
    
    inputContainer.addEventListener("focusin", () => {
      gsap.to(inputContainer, {
        boxShadow: "0 0 0 3px var(--accent-glow)",
        borderColor: "var(--accent)",
        duration: 0.2,
      });
    });
    
    inputContainer.addEventListener("focusout", () => {
      gsap.to(inputContainer, {
        boxShadow: "none",
        borderColor: "var(--border)",
        duration: 0.2,
      });
    });
  }, { scope: inputRef });

  return (
    <div className="px-4 pb-3 pt-2 ...">
      <div ref={suggestionsRef} className="mb-2 ...">
        {/* Suggestions */}
      </div>
      <div className="flex items-end gap-2 ...">
        <textarea ref={inputRef} ... />
        <button
          ref={sendBtnRef}
          className="... hover:scale-105 active:scale-95 ..."
          onClick={() => {
            handleSendPress();
            handleSubmit();
          }}
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
```

---

### 2.6 Header.tsx — Theme Toggle Animation

**Enhanced theme switch:**

```typescript
export default function Header() {
  const themeBtnRef = useRef<HTMLButtonElement>(null);
  const { state, dispatch } = useApp();

  const toggleTheme = useCallback(() => {
    const next = state.theme === "dark" ? "light" : "dark";
    
    // Animate theme button icon
    if (themeBtnRef.current) {
      const icon = themeBtnRef.current.querySelector("svg");
      gsap.to(icon, {
        rotation: "+=180",
        scale: 0,
        duration: 0.2,
        ease: "power2.in",
        onComplete: () => {
          dispatch({ type: "SET_THEME", payload: next });
          document.documentElement.dataset.theme = next;
          
          gsap.to(icon, {
            scale: 1,
            duration: 0.3,
            ease: "back.out(1.7)",
          });
        },
      });
    }
    
    // Flash effect on theme change
    gsap.fromTo(document.body,
      { opacity: 0.8 },
      { opacity: 1, duration: 0.3, ease: "power2.out" }
    );
  }, [state.theme, dispatch]);

  return (
    <header className="flex items-center h-12 px-3 gap-3 ...">
      {/* ... */}
      <button 
        ref={themeBtnRef}
        className="btn-icon" 
        onClick={toggleTheme}
      >
        {state.theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
      </button>
    </header>
  );
}
```

---

### 2.7 ShortcutsPanel.tsx — Modal Animation

**Enhanced modal entrance/exit:**

```typescript
export default function ShortcutsPanel({ open, onClose }: ShortcutsPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const backdropRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    if (!panelRef.current || !backdropRef.current) return;
    
    if (open) {
      // Backdrop fade in
      gsap.fromTo(backdropRef.current,
        { opacity: 0 },
        { opacity: 1, duration: 0.2 }
      );
      
      // Panel entrance — scale + fade + slide
      gsap.fromTo(panelRef.current,
        { 
          opacity: 0, 
          scale: 0.95, 
          y: -10,
          transformOrigin: "top right",
        },
        { 
          opacity: 1, 
          scale: 1, 
          y: 0,
          duration: 0.25, 
          ease: "back.out(1.5)",
        }
      );
      
      // Stagger shortcuts list
      const items = panelRef.current.querySelectorAll(".shortcut-item");
      gsap.from(items, {
        x: -20,
        opacity: 0,
        stagger: 0.05,
        duration: 0.2,
        delay: 0.1,
      });
    }
  }, { dependencies: [open] });

  if (!open) return null;

  return (
    <>
      <div 
        ref={backdropRef}
        className="fixed inset-0 z-40" 
        onClick={onClose} 
      />
      <div 
        ref={panelRef}
        className="fixed right-3 top-14 z-50 w-64 ..."
      >
        {/* ... */}
      </div>
    </>
  );
}
```

---

### 2.8 Logo.tsx — SVG Animation

**Add subtle idle animation to the logo:**

```typescript
export default function Logo({ size = 48, className }: LogoProps) {
  const logoRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    if (!logoRef.current) return;
    
    const arms = logoRef.current.querySelectorAll("use[href='#arm']");
    const core = logoRef.current.querySelectorAll("circle");
    
    // Subtle pulse on the core
    gsap.to(core, {
      scale: 1.05,
      opacity: 0.8,
      repeat: -1,
      yoyo: true,
      duration: 2,
      ease: "sine.inOut",
      transformOrigin: "center center",
    });
    
    // Gentle rotation hint (very subtle)
    gsap.to(logoRef.current, {
      rotation: 2,
      repeat: -1,
      yoyo: true,
      duration: 4,
      ease: "sine.inOut",
    });
  }, { scope: logoRef });

  return (
    <div
      ref={logoRef}
      className={cn("flex items-center justify-center shrink-0", className)}
      style={{ width: s, height: s, color: "var(--accent)" }}
    >
      <svg>
        {/* ... */}
      </svg>
    </div>
  );
}
```

---

### 2.9 StatusBar.tsx — Status Change Animation

**Animate status updates:**

```typescript
export default function StatusBar() {
  const { state } = useApp();
  const statusRef = useRef<HTMLDivElement>(null);
  const prevTokensRef = useRef(state.statusTokens);

  // Animate token count changes
  useGSAP(() => {
    if (state.statusTokens !== prevTokensRef.current) {
      const tokenEl = statusRef.current?.querySelector(".token-count");
      if (tokenEl) {
        gsap.fromTo(tokenEl,
          { scale: 1.2, color: "var(--accent)" },
          { 
            scale: 1, 
            color: "var(--text-tertiary)",
            duration: 0.4, 
            ease: "power2.out",
          }
        );
      }
      prevTokensRef.current = state.statusTokens;
    }
  }, { dependencies: [state.statusTokens] });

  // MCP status dot animation
  const mcpOk = state.mcpConnected === state.mcpTotal && state.mcpTotal > 0;
  
  useGSAP(() => {
    const dot = statusRef.current?.querySelector(".mcp-dot");
    if (!dot) return;
    
    if (mcpOk) {
      gsap.to(dot, {
        scale: 1,
        backgroundColor: "var(--success)",
        duration: 0.3,
      });
    } else {
      gsap.to(dot, {
        scale: 0.8,
        backgroundColor: "var(--text-tertiary)",
        duration: 0.3,
      });
    }
  }, { dependencies: [mcpOk] });

  return (
    <div ref={statusRef} className="flex items-center h-7 px-3 gap-3 ...">
      <span>Model: {state.currentModel || "none"}</span>
      <span className="token-count">Tokens: {state.statusTokens}</span>
      <span className="flex items-center gap-1">
        <span className={`mcp-dot inline-block w-[6px] h-[6px] rounded-full ...`} />
        MCP: {state.mcpConnected}/{state.mcpTotal}
      </span>
    </div>
  );
}
```

---

## 3. Performance Optimization

### 3.1 Transform-Only Animations

All animations use transform properties for GPU acceleration:

| Property | Use Case | GPU Accelerated |
|----------|----------|-----------------|
| `x`, `y` | Movement | ✅ |
| `scale` | Size changes | ✅ |
| `rotation` | Rotations | ✅ |
| `opacity` | Fade effects | ✅ |
| `autoAlpha` | Fade + visibility | ✅ |

**Avoided Properties:**
- `width`, `height` (except for expand/collapse with `overflow: hidden`)
- `top`, `left`, `margin`, `padding`

### 3.2 will-change Usage

Add `will-change` only to actively animating elements:

```css
.will-animate {
  will-change: transform, opacity;
}
```

Remove after animation completes:

```typescript
gsap.to(element, {
  // ... animation
  onComplete: () => {
    element.style.willChange = "auto";
  },
});
```

### 3.3 Stagger Optimization

Use GSAP stagger instead of individual tweens:

```typescript
// ❌ Bad: Individual tweens
items.forEach((item, i) => {
  gsap.from(item, { delay: i * 0.1, ... });
});

// ✅ Good: Stagger
gsap.from(items, { stagger: 0.1, ... });
```

### 3.4 Cleanup Strategy

All animations are automatically cleaned up via `useGSAP`:

```typescript
useGSAP(() => {
  // Animation setup
  gsap.to(element, { ... });
  
  // Cleanup happens automatically on unmount
  // No need for manual ctx.revert()
}, { scope: containerRef });
```

### 3.5 Reduced Motion Support

Global `gsap.matchMedia()` handles `prefers-reduced-motion`:

```typescript
mm.add(
  {
    reduceMotion: "(prefers-reduced-motion: reduce)",
  },
  (context) => {
    if (context.conditions.reduceMotion) {
      gsap.defaults({ duration: 0 });
    }
  }
);
```

---

## 4. Implementation Phases

### Phase 1: Foundation (Day 1)

1. Install dependencies
2. Create `src/lib/gsap.ts` configuration
3. Update `tailwind.config.ts` (remove conflicting animations)
4. Test reduced-motion support

### Phase 2: Core Components (Day 2-3)

1. **WelcomeScreen** — Full entrance sequence
2. **MessageList** — Message stagger animations
3. **ToolCard** — Expand/collapse animations

### Phase 3: Navigation (Day 4)

1. **Sidebar** — Show/hide + section animations
2. **Header** — Theme toggle animation
3. **ShortcutsPanel** — Modal animations

### Phase 4: Polish (Day 5)

1. **InputBar** — Micro-interactions
2. **Logo** — Idle animations
3. **StatusBar** — Status change animations
4. Performance testing and optimization

---

## 5. Testing Checklist

### Functionality

- [ ] All animations play correctly
- [ ] Animations don't block user interaction
- [ ] Reduced motion preference is respected
- [ ] No visual glitches or jumps

### Performance

- [ ] 60fps on desktop
- [ ] 60fps on mobile (or acceptable fallback)
- [ ] No layout thrashing
- [ ] Memory leaks checked (cleanup on unmount)

### Accessibility

- [ ] `prefers-reduced-motion: reduce` disables animations
- [ ] Screen readers not affected by animations
- [ ] Focus management preserved
- [ ] No seizure-inducing effects

### Browser Compatibility

- [ ] Chrome/Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Mobile browsers (iOS Safari, Chrome Android)

---

## 6. File Structure

```
web/src/
├── lib/
│   ├── gsap.ts          # NEW: GSAP configuration
│   └── utils.ts
├── components/
│   ├── WelcomeScreen.tsx # MODIFIED: GSAP animations
│   ├── MessageList.tsx   # MODIFIED: GSAP animations
│   ├── ToolCard.tsx      # MODIFIED: GSAP animations
│   ├── Sidebar.tsx       # MODIFIED: GSAP animations
│   ├── Header.tsx        # MODIFIED: GSAP animations
│   ├── InputBar.tsx      # MODIFIED: GSAP animations
│   ├── Logo.tsx          # MODIFIED: GSAP animations
│   ├── StatusBar.tsx     # MODIFIED: GSAP animations
│   └── ShortcutsPanel.tsx # MODIFIED: GSAP animations
└── ...
```

---

## 7. Bundle Size Impact

| Package | Size (gzipped) |
|---------|----------------|
| gsap | ~23KB |
| @gsap/react | ~2KB |
| **Total** | **~25KB** |

**Tree-shaking:** Import only what's needed:

```typescript
import { gsap } from "gsap";
import { useGSAP } from "@gsap/react";
// Don't import unused plugins
```

---

## 8. Rollback Plan

If issues arise:

1. **Immediate:** Comment out GSAP imports and restore CSS animations
2. **Quick fix:** Revert to previous commit
3. **Partial:** Disable GSAP per-component by removing `useGSAP` hooks

---

## Summary

This plan integrates GSAP incrementally, enhancing each component with professional animations while maintaining:

- **Performance:** Transform-only animations, GPU acceleration
- **Accessibility:** Reduced motion support via `gsap.matchMedia()`
- **Maintainability:** Automatic cleanup via `useGSAP` hook
- **Bundle size:** ~25KB addition (acceptable for animation quality)

Total estimated implementation time: **5 days** for full integration with testing.
