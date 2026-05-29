import { useState, useCallback, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api';
import type { SessionData } from '../types';

export function useSessions() {
  const { dispatch } = useApp();
  const [sessions, setSessions] = useState<SessionData[]>([]);
  const [confirmDelete, setConfirmDelete] = useState<{ type: string; id?: string; path?: string } | null>(null);
  const [editingSession, setEditingSession] = useState<string | null>(null);
  const [editName, setEditName] = useState('');

  const loadSessions = useCallback(() => {
    api.getSessions()
      .then((data) => setSessions(data.sessions || []))
      .catch((err) => console.error('Failed to load sessions:', err));
  }, []);

  const loadInitialData = useCallback(async () => {
    try {
      const [models, skills, mcp] = await Promise.all([
        api.getModels(),
        api.getSkills(),
        api.getMcp(),
      ]);
      dispatch({ type: 'SET_MODELS', payload: models });
      dispatch({ type: 'SET_SKILLS', payload: skills.skills || [] });
      dispatch({ type: 'SET_MCP', payload: mcp });

      const selected = (skills.skills || []).filter((s) => s.selected).map((s) => s.name);
      if (selected.length > 0) {
        dispatch({ type: 'SET_ACTIVE_SKILLS', payload: selected });
      }
    } catch (err) {
      console.error('Failed to load initial data:', err);
    }
  }, [dispatch]);

  useEffect(() => {
    loadInitialData();
    loadSessions();
    api.getRagDocuments()
      .then((data) => dispatch({ type: 'SET_RAG_DOCUMENTS', payload: data }))
      .catch((err) => console.error('Failed to load RAG documents:', err));
  }, [loadInitialData, loadSessions, dispatch]);

  const handleNewSession = async () => {
    try {
      const s = await api.createSession('新对话');
      setSessions((prev) => [s, ...prev]);
      dispatch({ type: 'CLEAR_MESSAGES' });
      dispatch({ type: 'SET_CURRENT_SESSION', payload: s.id });
    } catch (err) {
      console.error('Failed to create session:', err);
    }
  };

  const handleSwitchSession = async (id: string) => {
    dispatch({ type: 'SET_CURRENT_SESSION', payload: id });
    try {
      const data = await api.getSessionMessages(id);
      const messages = (data.messages || []).map((m, i) => ({
        id: crypto.randomUUID(),
        role: m.role as 'user' | 'assistant',
        content: m.content || '',
        blocks: m.role === 'assistant' ? [{ type: 'text' as const, content: m.content || '' }] : undefined,
        toolCalls: [],
        timestamp: Date.now() - (data.messages.length - i) * 1000,
      }));
      dispatch({ type: 'SET_MESSAGES', payload: messages });
    } catch (err) {
      console.error('Failed to switch session:', err);
      dispatch({ type: 'CLEAR_MESSAGES' });
    }
    loadSessions();
  };

  const handleRename = async (id: string) => {
    if (!editName.trim()) {
      setEditingSession(null);
      return;
    }
    try {
      await api.renameSession(id, editName.trim());
      setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, name: editName.trim() } : s)));
    } catch (err) {
      console.error('Failed to rename session:', err);
    }
    setEditingSession(null);
  };

  const handleDelete = async () => {
    if (!confirmDelete) return;
    try {
      if (confirmDelete.type === 'session' && confirmDelete.id) {
        await api.deleteSession(confirmDelete.id);
        setSessions((prev) => prev.filter((s) => s.id !== confirmDelete.id));
      } else if (confirmDelete.type === 'knowledge' && confirmDelete.path) {
        await api.deleteRagDocument(confirmDelete.path);
        api.getRagDocuments().then((data) => dispatch({ type: 'SET_RAG_DOCUMENTS', payload: data }));
      }
    } catch (err) {
      console.error('Failed to delete:', err);
    }
    setConfirmDelete(null);
  };

  return {
    sessions,
    confirmDelete,
    editingSession,
    editName,
    setConfirmDelete,
    setEditingSession,
    setEditName,
    handleNewSession,
    handleSwitchSession,
    handleRename,
    handleDelete,
    loadSessions,
  };
}
