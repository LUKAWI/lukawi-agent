import React, { useRef, useEffect } from 'react';
import { gsap } from '../lib/gsap';

interface ThinkingIndicatorProps {
  isVisible: boolean;
}

export default function ThinkingIndicator({ isVisible }: ThinkingIndicatorProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const dotsRef = useRef<(HTMLSpanElement | null)[]>([]);
  const textRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!containerRef.current || !isVisible) return;

    const tl = gsap.timeline({ repeat: -1 });

    dotsRef.current.forEach((dot, i) => {
      if (!dot) return;
      tl.to(dot, {
        y: -4,
        duration: 0.2,
        ease: 'power2.out',
      }, i * 0.15);
      tl.to(dot, {
        y: 0,
        duration: 0.2,
        ease: 'power2.in',
      }, i * 0.15 + 0.2);
    });

    if (textRef.current) {
      gsap.fromTo(textRef.current, 
        { opacity: 0.5 },
        { opacity: 1, duration: 1, repeat: -1, yoyo: true, ease: 'sine.inOut' }
      );
    }

    return () => {
      tl.kill();
      gsap.killTweensOf(textRef.current);
    };
  }, [isVisible]);

  if (!isVisible) return null;

  return (
    <div 
      ref={containerRef}
      className="inline-flex items-center gap-1.5 px-3 py-2 text-[13px] text-[var(--text-secondary)]"
    >
      <span ref={textRef}>Thinking</span>
      <span className="flex gap-0.5">
        <span 
          ref={el => dotsRef.current[0] = el}
          className="inline-block w-1 h-1 rounded-full bg-[var(--text-secondary)]"
        />
        <span 
          ref={el => dotsRef.current[1] = el}
          className="inline-block w-1 h-1 rounded-full bg-[var(--text-secondary)]"
        />
        <span 
          ref={el => dotsRef.current[2] = el}
          className="inline-block w-1 h-1 rounded-full bg-[var(--text-secondary)]"
        />
      </span>
    </div>
  );
}
