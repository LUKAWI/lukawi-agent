import React, { useRef } from 'react';
import { useGSAP, gsap, getDuration } from '../lib/gsap';

export default function ShortcutsPanel({ open, onClose }: { open: boolean; onClose: () => void }) {
  const panelRef = useRef<HTMLDivElement>(null);
  const backdropRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    if (!open || !panelRef.current || !backdropRef.current) return;

    gsap.fromTo(backdropRef.current, 
      { opacity: 0 }, 
      { opacity: 1, duration: getDuration(0.2) }
    );

    gsap.fromTo(panelRef.current, 
      { opacity: 0, scale: 0.95, y: -10, transformOrigin: "top right" }, 
      { opacity: 1, scale: 1, y: 0, duration: getDuration(0.25), ease: "back.out(1.5)" }
    );

    gsap.from(panelRef.current.querySelectorAll('.shortcut-item'), 
      { x: -20, opacity: 0, stagger: 0.05, duration: getDuration(0.2), delay: 0.1 }
    );
  }, { dependencies: [open] });

  if (!open) return null;

  const shortcuts = [
    { key: 'Ctrl+B', desc: 'Toggle sidebar' },
    { key: 'Ctrl+L', desc: 'Clear chat' },
    { key: 'Enter', desc: 'Send message' },
    { key: 'Shift + Enter', desc: 'New line' },
    { key: '/', desc: 'Command mode' },
  ];

  return (
    <>
      <div ref={backdropRef} className="fixed inset-0 z-40" onClick={onClose} />
      <div ref={panelRef} className="fixed right-3 top-14 z-50 w-64 border border-[var(--border)] rounded-[10px] bg-[var(--surface)] shadow-md p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-[13px] font-semibold text-[var(--text)]">Keyboard Shortcuts</h3>
          <button className="btn-icon" onClick={onClose} aria-label="Close">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="space-y-2">
          {shortcuts.map((s) => (
            <div key={s.key} className="shortcut-item flex items-center justify-between text-[12px]">
              <kbd className="px-1.5 py-0.5 rounded-[4px] text-[11px] font-mono font-semibold border border-[var(--border)] border-b-2 bg-[var(--surface-alt)] text-[var(--text)] min-w-[60px] text-center">
                {s.key}
              </kbd>
              <span className="text-[var(--text-secondary)]">{s.desc}</span>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
