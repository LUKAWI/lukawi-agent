import React, { useRef } from 'react';
import { useSSE } from '../hooks/useSSE';
import { useGSAP, gsap, getDuration } from '../lib/gsap';
import Logo from './Logo';

const EXAMPLES = [
  'What can you do?',
  'Help me write code',
  'Search the web for latest news',
];

export default function WelcomeScreen() {
  const { sendMessage } = useSSE();
  const containerRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });

    tl.from('.welcome-logo', {
      scale: 0,
      rotation: -180,
      duration: getDuration(0.8),
      ease: 'back.out(1.7)',
    });

    tl.from('.welcome-title', {
      y: 30,
      opacity: 0,
      duration: getDuration(0.5),
    }, '-=0.3');

    tl.from('.welcome-desc', {
      y: 20,
      opacity: 0,
      duration: getDuration(0.4),
    }, '-=0.2');

    tl.from('.welcome-example > *', {
      y: 20,
      opacity: 0,
      scale: 0.9,
      duration: getDuration(0.4),
      ease: 'back.out(1.5)',
      stagger: 0.1,
      clearProps: 'all',
    }, '-=0.2');

    tl.from('.welcome-version', {
      opacity: 0,
      duration: getDuration(0.3),
    }, '-=0.1');
  }, { scope: containerRef });

  return (
    <div ref={containerRef} className="flex-1 flex flex-col items-center justify-center px-6 py-8">
      <div className="flex flex-col items-center gap-5 max-w-[400px] w-full text-center">
        <Logo size={56} className="welcome-logo" />
        <h1 className="welcome-title font-sans text-display text-[var(--text)]">
          Lukawi Agent
        </h1>
        <p className="welcome-desc text-[15px] text-[var(--text-secondary)] leading-relaxed max-w-[340px]">
          Your AI assistant with tools. Ask questions, write code, browse the web, and more.
        </p>
        <div className="welcome-example flex flex-wrap justify-center gap-2 mt-3">
          {EXAMPLES.map((text) => (
            <button
              key={text}
              className="px-5 py-2.5 text-[13px] font-medium font-sans text-[var(--text)] bg-[var(--surface)] border border-[var(--border)] rounded-[10px] cursor-pointer hover:bg-[var(--accent-light)] hover:border-[var(--accent)] hover:text-[var(--accent)] hover:-translate-y-0.5 active:translate-y-0 transition-all"
              onClick={() => sendMessage(text)}
            >
              {text}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
