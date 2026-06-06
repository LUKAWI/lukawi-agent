import React, { useRef } from 'react';
import { cn } from '../lib/utils';
import { gsap, useGSAP } from '../lib/gsap';

interface LogoProps {
  size?: number;
  className?: string;
}

// Lukawi Agent Logo — 6-fold rotational symmetry
export default function Logo({ size = 48, className }: LogoProps) {
  const s = size;
  const logoRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    if (!logoRef.current) return;

    const circles = logoRef.current.querySelectorAll('circle');
    const mm = gsap.matchMedia();

    mm.add('(prefers-reduced-motion: no-preference)', () => {
      gsap.to(circles, {
        scale: 1.05,
        opacity: 0.8,
        repeat: -1,
        yoyo: true,
        duration: 2,
        ease: 'sine.inOut',
        transformOrigin: 'center center',
      });

      gsap.to(logoRef.current, {
        rotation: 2,
        repeat: -1,
        yoyo: true,
        duration: 4,
        ease: 'sine.inOut',
      });
    });

    return () => {
      mm.revert();
    };
  }, { scope: logoRef });

  return (
    <div
      ref={logoRef}
      className={cn('flex items-center justify-center shrink-0', className)}
      style={{ width: s, height: s, color: 'var(--accent)' }}
      role="img"
      aria-label="Lukawi Agent"
    >
      <svg
        width={s}
        height={s}
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Outer curved arm with terminal node */}
          <g id="arm">
            <path
              d="M32 7 C40 7, 48 18, 44 30 C42 36, 36 41, 32 41"
              stroke="currentColor"
              strokeWidth="3.5"
              strokeLinecap="round"
            />
            <path
              d="M34 11 C40 12, 44 20, 40 28"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              opacity="0.35"
            />
            <circle cx="44" cy="30" r="3.5" fill="currentColor" />
          </g>

          {/* Inner depth arc */}
          <g id="arc">
            <path
              d="M32 15 C34 15, 40 20, 40 28"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              opacity="0.2"
            />
          </g>
        </defs>

        {/* 6 outer arms */}
        <use href="#arm" />
        <use href="#arm" transform="rotate(60 32 32)" />
        <use href="#arm" transform="rotate(120 32 32)" />
        <use href="#arm" transform="rotate(180 32 32)" />
        <use href="#arm" transform="rotate(240 32 32)" />
        <use href="#arm" transform="rotate(300 32 32)" />

        {/* 6 inner arcs */}
        <use href="#arc" />
        <use href="#arc" transform="rotate(60 32 32)" />
        <use href="#arc" transform="rotate(120 32 32)" />
        <use href="#arc" transform="rotate(180 32 32)" />
        <use href="#arc" transform="rotate(240 32 32)" />
        <use href="#arc" transform="rotate(300 32 32)" />

        {/* Core */}
        <circle cx="32" cy="32" r="5" fill="currentColor" opacity="0.9" />
        <circle cx="32" cy="32" r="2.5" fill="currentColor" />
      </svg>
    </div>
  );
}
