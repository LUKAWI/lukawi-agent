import React from 'react';
import { useSSE } from '../hooks/useSSE';
import Logo from './Logo';

const EXAMPLES = [
  'What can you do?',
  'Help me write code',
  'Search the web for latest news',
];

export default function WelcomeScreen() {
  const { sendMessage } = useSSE();

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6 py-8 animate-[fade-in_400ms_ease]">
      <div className="flex flex-col items-center gap-5 max-w-[400px] w-full text-center">
        <Logo size={56} />
        <h1 className="font-sans text-display text-[var(--text)]">
          Lukawi Agent
        </h1>
        <p className="text-[15px] text-[var(--text-secondary)] leading-relaxed max-w-[340px]">
          Your AI assistant with tools. Ask questions, write code, browse the web, and more.
        </p>
        <div className="flex flex-wrap justify-center gap-2 mt-3">
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
      <div className="absolute bottom-4 text-[12px] font-medium text-[var(--text-tertiary)]">
        v0.2.0
      </div>
    </div>
  );
}
