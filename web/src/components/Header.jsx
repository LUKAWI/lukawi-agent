import React from 'react';
import { MenuIcon, MoonIcon, SunIcon } from './icons';
import './Header.css';

export default function Header({ currentModel, theme, onToggleSidebar, onToggleTheme, models, onModelChange }) {
  return (
    <header className="app-header">
      <button className="header-btn" onClick={onToggleSidebar} aria-label="Toggle sidebar">
        <MenuIcon />
      </button>
      <span className="header-title">Lukawi Agent</span>
      <div className="header-right">
        <select
          className="header-model-select"
          value={currentModel}
          onChange={(e) => onModelChange(e.target.value)}
          aria-label="Select model"
        >
          {!currentModel && <option value="" disabled>Select model</option>}
          {models.map((m) => (
            <option key={m.name} value={m.name}>
              {m.model !== m.name ? `${m.name} (${m.model})` : m.name}
            </option>
          ))}
        </select>
        <button className="header-btn" onClick={onToggleTheme} aria-label="Toggle theme">
          {theme === 'dark' ? <MoonIcon /> : <SunIcon />}
        </button>
      </div>
    </header>
  );
}
