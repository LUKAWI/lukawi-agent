import React, { useEffect, useCallback } from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { api } from './api';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatPanel from './components/ChatPanel';
import StatusBar from './components/StatusBar';
import ShortcutsPanel from './components/ShortcutsPanel';
import type { StatusData } from './types';
import './globals.css';

function AppContent() {
  const { state, dispatch } = useApp();

  useEffect(() => {
    Promise.all([
      api.getConfig().catch(() => ({ theme: 'light' as const })),
      api.getStatus().catch(() => ({}) as StatusData),
    ]).then(([cfg, status]) => {
      const theme = cfg.theme || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
      dispatch({ type: 'SET_THEME', payload: theme as 'light' | 'dark' });
      if (status.model) dispatch({ type: 'SET_CURRENT_MODEL', payload: status.model });
    });
  }, [dispatch]);

  useEffect(() => {
    document.documentElement.dataset.theme = state.theme;
  }, [state.theme]);

  const handleClear = useCallback(() => {
    dispatch({ type: 'CLEAR_MESSAGES' });
  }, [dispatch]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'b') { e.preventDefault(); dispatch({ type: 'TOGGLE_SIDEBAR' }); }
      if (e.ctrlKey && e.key === 'l') { e.preventDefault(); handleClear(); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [dispatch, handleClear]);

  return (
    <>
      <Header />
      <div className="flex-1 flex overflow-hidden min-h-0">
        <Sidebar />
        <ChatPanel />
      </div>
      <StatusBar />
      <ShortcutsPanel
        open={state.detailPanelOpen}
        onClose={() => dispatch({ type: 'TOGGLE_DETAIL_PANEL' })}
      />
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
