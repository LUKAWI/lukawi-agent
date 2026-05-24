import React from 'react';
import { MenuIcon, MoonIcon, SunIcon } from './icons';
import './Header.css';

export default function Header({ theme, onToggleSidebar, onToggleTheme }) {
  return (
    <header className="app-header">
      <button className="header-btn" onClick={onToggleSidebar} aria-label="Toggle sidebar">
        <MenuIcon />
      </button>
      <span className="header-title">Lukawi Agent</span>
      <div className="header-right">
        <button className="header-btn" onClick={onToggleTheme} aria-label="Toggle theme">
          {theme === 'dark' ? <MoonIcon /> : <SunIcon />}
        </button>
      </div>
    </header>
  );
}
