import React, { useState, useCallback, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { useSSE } from '../hooks/useSSE';
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

  return (
    <div className="px-4 pb-3 pt-2 border-t border-[var(--border-light)] bg-[var(--surface)]">
      {suggestions.length > 0 && (
        <div className="mb-2 border border-[var(--border)] rounded-[10px] bg-[var(--surface)] shadow-md overflow-hidden">
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
      <div className="flex items-end gap-2 bg-[var(--bg)] border-[1.5px] border-[var(--border)] rounded-[10px] px-3 py-2 transition-colors focus-within:border-[var(--accent)] focus-within:shadow-[0_0_0_3px_var(--accent-glow)]">
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
