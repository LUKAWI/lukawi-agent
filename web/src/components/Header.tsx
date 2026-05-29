import React, { useRef, useCallback } from 'react';
import { cn } from '../lib/utils';
import { useApp } from '../context/AppContext';
import { Menu, Sun, Moon, Keyboard } from 'lucide-react';
import Logo from './Logo';
import { gsap, getDuration } from '../lib/gsap';

export default function Header() {
  const { state, dispatch } = useApp();
  const themeBtnRef = useRef<HTMLButtonElement>(null);

  const toggleTheme = useCallback(() => {
    const btn = themeBtnRef.current;
    if (!btn) return;

    const icon = btn.querySelector('svg');
    if (!icon) return;

    gsap.to(icon, {
      rotation: "+=180",
      scale: 0,
      duration: getDuration(0.2),
      ease: "power2.in",
      onComplete: () => {
        const next = state.theme === 'dark' ? 'light' : 'dark';
        dispatch({ type: 'SET_THEME', payload: next });
        document.documentElement.dataset.theme = next;

        gsap.to(icon, {
          scale: 1,
          duration: getDuration(0.3),
          ease: "back.out(1.7)"
        });

        gsap.fromTo(document.body,
          { opacity: 0.8 },
          { opacity: 1, duration: getDuration(0.3), ease: "power2.out" }
        );
      }
    });
  }, [state.theme, dispatch]);

  const toggleShortcuts = () => {
    dispatch({ type: 'TOGGLE_DETAIL_PANEL' });
  };

  return (
    <header className="flex items-center h-12 px-3 gap-3 shrink-0 border-b border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-xs)] z-30">
      <button
        className="btn-icon"
        onClick={() => dispatch({ type: 'TOGGLE_SIDEBAR' })}
        aria-label="Toggle sidebar"
      >
        <Menu size={18} />
      </button>

      <Logo size={22} className="mr-0.5" />
      <span className="font-sans text-sm font-semibold text-[var(--text)] select-none">
        Lukawi Agent
      </span>

      <div className="ml-auto flex items-center gap-1">
        <button className="btn-icon" onClick={toggleShortcuts} aria-label="Shortcuts" title="Shortcuts">
          <Keyboard size={16} />
        </button>
        <button ref={themeBtnRef} className="btn-icon" onClick={toggleTheme} aria-label="Toggle theme">
          {state.theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        </button>
      </div>
    </header>
  );
}
