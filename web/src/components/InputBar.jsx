import React, { useState, useCallback, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { useSSE } from '../hooks/useSSE';
import { SendIcon } from './icons';
import './InputBar.css';

const KNOWN_COMMANDS = ['/help', '/clear', '/models', '/models use', '/skill list', '/skill load', '/skill active', '/mcp list', '/mcp connect', '/mcp disconnect', '/quit'];

export default function InputBar() {
  const { state } = useApp();
  const { sendMessage, isLoading } = useSSE();
  const [value, setValue] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const inputRef = useRef(null);

  const autoResize = useCallback((el) => {
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, []);

  const handleChange = useCallback((e) => {
    const v = e.target.value;
    setValue(v);
    autoResize(e.target);

    if (v.startsWith('/')) {
      setSuggestions(KNOWN_COMMANDS.filter(c => c.startsWith(v)));
    } else {
      setSuggestions([]);
    }
  }, [autoResize]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }, [value, isLoading]);

  const handleSubmit = useCallback(() => {
    const text = value.trim();
    if (!text || isLoading) return;
    setValue('');
    setSuggestions([]);
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
    }
    sendMessage(text);
  }, [value, isLoading, sendMessage]);

  const selectSuggestion = useCallback((cmd) => {
    setValue(cmd + ' ');
    setSuggestions([]);
    if (inputRef.current) {
      inputRef.current.focus();
      autoResize(inputRef.current);
    }
  }, [autoResize]);

  return (
    <div className="input-bar">
      {suggestions.length > 0 && (
        <div className="autocomplete" role="listbox" aria-label="Command suggestions">
          {suggestions.map((s) => (
            <div
              key={s}
              className="autocomplete-item"
              role="option"
              aria-selected={false}
              onClick={() => selectSuggestion(s)}
            >
              {s}
            </div>
          ))}
        </div>
      )}
      <div className="input-row">
        <textarea
          ref={inputRef}
          className="chat-input"
          placeholder={isLoading ? 'Waiting for response...' : 'Send a message...'}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          rows={1}
          aria-label="Message input"
        />
        <button
          className="send-btn"
          onClick={handleSubmit}
          disabled={isLoading || !value.trim()}
          aria-label="Send message"
        >
          <SendIcon size={18} />
        </button>
      </div>
    </div>
  );
}
