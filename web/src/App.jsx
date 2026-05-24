import React, { useEffect, useCallback } from 'react';
import { AppProvider, useApp } from './context/AppContext';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatPanel from './components/ChatPanel';

import { api } from './api';
import './App.css';

function AppContent() {
  const { state, dispatch } = useApp();

  useEffect(() => {
    // Load initial state
    Promise.all([
      api.getConfig().catch(() => ({ theme: 'light' })),
      api.getStatus().catch(() => ({})),
    ]).then(([cfg, status]) => {
      if (cfg.theme) dispatch({ type: 'SET_THEME', payload: cfg.theme });
      if (status.model) dispatch({ type: 'SET_CURRENT_MODEL', payload: status.model });
    });
  }, [dispatch]);

  // Sync theme to <html> element so CSS variables apply to body
  useEffect(() => {
    document.documentElement.dataset.theme = state.theme;
  }, [state.theme]);

  const handleToggleTheme = useCallback(() => {
    const next = state.theme === 'dark' ? 'light' : 'dark';
    dispatch({ type: 'SET_THEME', payload: next });
    api.setTheme(next).catch(() => {});
  }, [state.theme, dispatch]);

  const handleToggleSidebar = useCallback(() => {
    dispatch({ type: 'TOGGLE_SIDEBAR' });
  }, [dispatch]);

  const handleClear = useCallback(() => {
    dispatch({ type: 'CLEAR_MESSAGES' });
  }, [dispatch]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e) => {
      if (e.ctrlKey && e.key === 'b') { e.preventDefault(); handleToggleSidebar(); }
      if (e.ctrlKey && e.key === 'l') { e.preventDefault(); handleClear(); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [handleToggleSidebar, handleClear]);

  return (
    <>
      <Header
        theme={state.theme}
        onToggleSidebar={handleToggleSidebar}
        onToggleTheme={handleToggleTheme}
      />
      <div className="main-content">
        <Sidebar />
        <ChatPanel />
      </div>

    </>
  );
}

export default function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}