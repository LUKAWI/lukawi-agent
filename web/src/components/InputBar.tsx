import React, { useState, useCallback, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { useSSE } from '../hooks/useSSE';
import { gsap, useGSAP, getDuration } from '../lib/gsap';
import { Send } from 'lucide-react';

const KNOWN_COMMANDS = [
  '/help', '/clear', '/models', '/models use',
  '/skill list', '/skill load', '/skill active',
  '/mcp list', '/mcp connect', '/mcp disconnect', '/quit',
];

export default function InputBar() {
  const { state } = useApp();
  const { sendMessage, isLoading } = useSSE();
  const [value, setValue] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const sendBtnRef = useRef<HTMLButtonElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const inputContainerRef = useRef<HTMLDivElement>(null);

  const autoResize = useCallback((el: HTMLTextAreaElement) => {
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, []);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const v = e.target.value;
      setValue(v);
      autoResize(e.target);

      if (v.startsWith('/')) {
        setSuggestions(KNOWN_COMMANDS.filter((c) => c.startsWith(v)));
      } else {
        setSuggestions([]);
      }
    },
    [autoResize],
  );

  const handleSubmit = useCallback(() => {
    const text = value.trim();
    if (!text || isLoading) return;

    if (sendBtnRef.current) {
      gsap.to(sendBtnRef.current, {
        scale: 0.85,
        duration: getDuration(0.1),
        ease: 'power2.in',
        onComplete: () => {
          gsap.to(sendBtnRef.current!, {
            scale: 1,
            duration: getDuration(0.3),
            ease: 'elastic.out(1, 0.3)',
          });
        },
      });
    }

    setValue('');
    setSuggestions([]);
    if (inputRef.current) inputRef.current.style.height = 'auto';
    sendMessage(text);
  }, [value, isLoading, sendMessage]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit],
  );

  useGSAP(
    () => {
      if (!suggestionsRef.current || suggestions.length === 0) return;
      const items = suggestionsRef.current.children;
      if (items.length === 0) return;

      gsap.from(items, {
        y: -10,
        opacity: 0,
        stagger: 0.05,
        duration: getDuration(0.2),
        ease: 'power2.out',
      });
    },
    { dependencies: [suggestions.length], scope: suggestionsRef },
  );

  useGSAP(
    () => {
      const container = inputContainerRef.current;
      if (!container) return;

      const onFocus = () => {
        gsap.to(container, {
          boxShadow: '0 0 0 3px var(--accent-glow)',
          borderColor: 'var(--accent)',
          duration: getDuration(0.2),
        });
      };

      const onBlur = () => {
        gsap.to(container, {
          boxShadow: 'none',
          borderColor: 'var(--border)',
          duration: getDuration(0.2),
        });
      };

      container.addEventListener('focusin', onFocus);
      container.addEventListener('focusout', onBlur);

      return () => {
        container.removeEventListener('focusin', onFocus);
        container.removeEventListener('focusout', onBlur);
      };
    },
    { scope: inputContainerRef },
  );

  return (
    <div className="px-4 pb-3 pt-2 border-t border-[var(--border-light)] bg-[var(--surface)]">
      {suggestions.length > 0 && (
        <div
          ref={suggestionsRef}
          className="mb-2 border border-[var(--border)] rounded-[10px] bg-[var(--surface)] shadow-md overflow-hidden"
        >
          {suggestions.map((s) => (
            <div
              key={s}
              className="px-3.5 py-2 cursor-pointer font-mono text-[13px] text-[var(--text-secondary)] hover:bg-[var(--accent-light)] hover:text-[var(--accent)] transition-colors border-b border-[var(--border-light)] last:border-b-0"
              onClick={() => {
                setValue(s + ' ');
                setSuggestions([]);
                inputRef.current?.focus();
              }}
            >
              {s}
            </div>
          ))}
        </div>
      )}
      <div
        ref={inputContainerRef}
        className="flex items-center gap-2 bg-[var(--bg)] border-[1.5px] border-[var(--border)] rounded-[10px] px-3 py-2 transition-colors"
      >
        <textarea
          ref={inputRef}
          className="flex-1 bg-transparent border-none outline-none font-sans text-[14px] leading-relaxed text-[var(--text)] resize-none min-h-[22px] max-h-[160px] placeholder:text-[var(--text-placeholder)]"
          placeholder={isLoading ? 'Waiting for response...' : 'Send a message...'}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          rows={1}
          aria-label="Message input"
        />
        <button
          ref={sendBtnRef}
          className="flex items-center justify-center w-[36px] h-[36px] shrink-0 rounded-full bg-[var(--accent)] text-white shadow-sm hover:bg-[var(--accent-hover)] hover:scale-105 active:scale-95 disabled:opacity-35 disabled:cursor-not-allowed disabled:scale-100 transition-all"
          onClick={handleSubmit}
          disabled={isLoading || !value.trim()}
          aria-label="Send message"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
