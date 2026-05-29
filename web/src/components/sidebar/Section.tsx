import React, { useState, useRef } from 'react';
import { cn } from '../../lib/utils';
import { useGSAP, gsap, getDuration } from '../../lib/gsap';
import { ChevronRight } from 'lucide-react';

export interface SectionProps {
  title: string;
  icon: React.ReactNode;
  defaultOpen?: boolean;
  badge?: string | number;
  variant?: 'default' | 'highlighted';
  children: React.ReactNode;
}

export function Section({ title, icon, defaultOpen = false, badge, variant = 'default', children }: SectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  const sectionRef = useRef<HTMLDivElement>(null);
  const chevronRef = useRef<SVGSVGElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const itemsRef = useRef<HTMLDivElement[]>([]);

  useGSAP(() => {
    if (!chevronRef.current || !contentRef.current) return;

    gsap.to(chevronRef.current, {
      rotation: open ? 90 : 0,
      duration: getDuration(0.2),
      ease: "power2.out",
    });

    gsap.to(contentRef.current, {
      height: open ? "auto" : 0,
      duration: getDuration(0.3),
      ease: "power2.inOut",
    });

    if (open && itemsRef.current.length > 0) {
      gsap.fromTo(
        itemsRef.current.filter(Boolean),
        { opacity: 0, y: -10 },
        { opacity: 1, y: 0, duration: getDuration(0.2), stagger: 0.05, ease: "power2.out" }
      );
    }
  }, { scope: sectionRef, dependencies: [open] });

  const isHighlighted = variant === 'highlighted';

  return (
    <div ref={sectionRef} className="mb-1">
      <button
        className={cn(
          'flex items-center gap-1.5 w-full px-2 py-1.5 text-[11px] font-semibold uppercase tracking-[0.06em] rounded-[6px] transition-colors',
          isHighlighted
            ? 'text-[var(--accent)] bg-[var(--accent-light)] hover:bg-[var(--accent-light)]'
            : 'text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] hover:bg-[var(--surface-alt)]',
        )}
        onClick={() => setOpen(!open)}
      >
        <ChevronRight
          ref={chevronRef}
          size={12}
        />
        <span className="opacity-70 shrink-0">{icon}</span>
        {title}
        {badge !== undefined && (
          <span className={cn(
            'ml-auto text-[10px] font-medium px-1.5 py-0.5 rounded-[3px]',
            isHighlighted
              ? 'text-[var(--accent)] bg-[var(--accent-light)]'
              : 'text-[var(--text-tertiary)] bg-[var(--surface-alt)]',
          )}>
            {badge}
          </span>
        )}
      </button>
      <div
        ref={contentRef}
        className="overflow-hidden"
        style={{ height: defaultOpen ? 'auto' : 0 }}
      >
        {children}
      </div>
    </div>
  );
}
