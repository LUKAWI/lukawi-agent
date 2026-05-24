import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api';
import {
  ModelIcon,
  SkillIcon,
  MCPIcon,
  HistoryIcon,
  DocumentIcon,
  ChevronRightIcon,
  CloseIcon,
  CheckIcon,
} from './icons';
import './Sidebar.css';

export default function Sidebar() {
  const { state, dispatch } = useApp();
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [showSessions, setShowSessions] = useState(true);
  const [showSkills, setShowSkills] = useState(false);
  const [showMemory, setShowMemory] = useState(false);
  const [showKnowledge, setShowKnowledge] = useState(false);
  const [showMcp, setShowMcp] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [memoryQuery, setMemoryQuery] = useState('');
  const [memoryResults, setMemoryResults] = useState([]);
  const [memorySearching, setMemorySearching] = useState(false);
  const [memoryError, setMemoryError] = useState(null);
  const searchTimerRef = useRef(null);
  const fileInputRef = useRef(null);
  const initialLoadRef = useRef(true);

  useEffect(() => {
    api.getModels().then(data => dispatch({ type: 'SET_MODELS', payload: data })).catch(() => {});
    api.getSkills().then(data => {
      dispatch({ type: 'SET_SKILLS', payload: data.skills });
      const selected = data.skills.filter(s => s.selected).map(s => s.name);
      if (selected.length > 0) {
        dispatch({ type: 'SET_ACTIVE_SKILLS', payload: selected });
      }
    }).catch(() => {});
    api.getMcp().then(data => dispatch({ type: 'SET_MCP', payload: data })).catch(() => {});
  }, [dispatch]);

  useEffect(() => {
    api.getSessions().then(async (data) => {
      setSessions(data.sessions || []);
      if (initialLoadRef.current && data.sessions && data.sessions.length > 0 && !state.currentSessionId) {
        const firstId = data.sessions[0].id;
        dispatch({ type: 'SET_CURRENT_SESSION', payload: firstId });
        try {
          const msgData = await api.getSessionMessages(firstId);
          const messages = (msgData.messages || []).map((m, i) => ({
            id: crypto.randomUUID(),
            role: m.role,
            content: m.content || '',
            blocks: m.role === 'assistant' ? [{ type: 'text', content: m.content || '' }] : undefined,
            toolCalls: [],
            timestamp: Date.now() - (msgData.messages.length - i) * 1000,
          }));
          dispatch({ type: 'SET_MESSAGES', payload: messages });
        } catch {}
      }
      initialLoadRef.current = false;
    }).catch(() => {});
    api.getRagDocuments().then(data => dispatch({ type: 'SET_RAG_DOCUMENTS', payload: data })).catch(() => {});
  }, [dispatch]);

  const searchRequestId = useRef(0);

  useEffect(() => {
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    setMemoryError(null);
    if (!memoryQuery.trim()) { setMemoryResults([]); return; }
    setMemorySearching(true);
    const reqId = ++searchRequestId.current;
    searchTimerRef.current = setTimeout(async () => {
      try {
        const data = await api.searchMemory(memoryQuery, 10, state.currentSessionId);
        if (reqId !== searchRequestId.current) return;
        setMemoryResults(data.memories || []);
        setMemoryError(null);
      } catch (err) {
        if (reqId !== searchRequestId.current) return;
        setMemoryResults([]);
        setMemoryError(err.message || 'Search failed');
      }
      setMemorySearching(false);
    }, 400);
    return () => { if (searchTimerRef.current) clearTimeout(searchTimerRef.current); };
  }, [memoryQuery]);

  useEffect(() => {
    if (!confirmDelete) return;
    const handler = (e) => {
      if (e.target.closest('.sidebar-confirm') || e.target.closest('.sidebar-session-delete')) return;
      setConfirmDelete(null);
    };
    document.addEventListener('click', handler);
    return () => document.removeEventListener('click', handler);
  }, [confirmDelete]);

  const handleCancelSearch = useCallback(() => {
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    searchRequestId.current++;
    setMemorySearching(false);
    setMemoryQuery('');
    setMemoryResults([]);
    setMemoryError(null);
  }, []);

  const refreshSessions = useCallback(() => {
    api.getSessions().then(data => setSessions(data.sessions || [])).catch(() => {});
  }, []);

  const refreshDocs = useCallback(() => {
    api.getRagDocuments().then(data => dispatch({ type: 'SET_RAG_DOCUMENTS', payload: data })).catch(() => {});
  }, [dispatch]);

  const handleModelChange = async (name) => {
    try {
      await api.useModel(name);
      dispatch({ type: 'SET_CURRENT_MODEL', payload: name });
    } catch (e) {
      console.error('Failed to switch model:', e);
    }
  };

  const handleSkillToggle = async (name) => {
    const enabled = !state.activeSkills.includes(name);
    try {
      await api.toggleSkill(name, enabled);
      dispatch({ type: 'TOGGLE_ACTIVE_SKILL', payload: name });
    } catch (e) {
      console.error('Failed to toggle skill:', e);
    }
  };

  const handleNewSession = async () => {
    try {
      const s = await api.createSession('新对话');
      setSessions(prev => [s, ...prev]);
      dispatch({ type: 'CLEAR_MESSAGES' });
      dispatch({ type: 'SET_CURRENT_SESSION', payload: s.id });
    } catch (e) {
      console.error('Failed to create session:', e);
    }
  };

  const handleSwitchSession = async (id) => {
    dispatch({ type: 'SET_CURRENT_SESSION', payload: id });
    try {
      const data = await api.getSessionMessages(id);
      const messages = (data.messages || []).map((m, i) => ({
        id: crypto.randomUUID(),
        role: m.role,
        content: m.content || '',
        blocks: m.role === 'assistant' ? [{ type: 'text', content: m.content || '' }] : undefined,
        toolCalls: [],
        timestamp: Date.now() - (data.messages.length - i) * 1000,
      }));
      dispatch({ type: 'SET_MESSAGES', payload: messages });
    } catch (e) {
      dispatch({ type: 'CLEAR_MESSAGES' });
    }
    refreshSessions();
  };

  const handleDeleteSession = async (id) => {
    setConfirmDelete({ type: 'session', id });
  };

  const handleConfirmDelete = async () => {
    if (!confirmDelete) return;
    try {
      if (confirmDelete.type === 'session') {
        await api.deleteSession(confirmDelete.id);
        setSessions(prev => prev.filter(s => s.id !== confirmDelete.id));
      } else if (confirmDelete.type === 'knowledge') {
        await api.deleteRagDocument(confirmDelete.path);
        refreshDocs();
      }
    } catch (e) {
      console.error('Failed to delete:', e);
    }
    setConfirmDelete(null);
  };

  const handleCancelDelete = () => {
    setConfirmDelete(null);
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      await api.uploadRagDocument(file);
      refreshDocs();
    } catch (err) {
      setUploadError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDeleteDoc = (sourcePath) => {
    setConfirmDelete({ type: 'knowledge', path: sourcePath });
  };

  const handleToggleKnowledgeSource = (sourcePath) => {
    dispatch({ type: 'TOGGLE_KNOWLEDGE_SOURCE', payload: sourcePath });
  };

  const formatTime = (ts) => {
    if (!ts) return '';
    const d = new Date(ts);
    return d.toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Asia/Shanghai',
    });
  };

  return (
    <aside className={`sidebar ${state.sidebarVisible ? 'open' : ''}`}>
      <div className="sidebar-inner">
      <div className="sidebar-section">
        <h3 className="section-title">
          <ModelIcon size={14} className="section-title-icon" />
          Models
        </h3>
        {state.models.map((m) => (
          <div
            key={m.name}
            className={`sidebar-item ${m.name === state.currentModel ? 'active' : ''}`}
            onClick={() => handleModelChange(m.name)}
          >
            <span className="item-bullet">
              <ModelIcon size={14} />
            </span>
            <span className="item-name">{m.model || m.name}</span>
            <span className="item-provider">{m.provider}</span>
          </div>
        ))}
        {state.models.length === 0 && <div className="sidebar-empty">No models available</div>}
      </div>

      {/* ── Skills ── */}
      <div className="sidebar-section">
        <h3
          className="section-title section-title-clickable"
          onClick={() => setShowSkills(!showSkills)}
        >
          <span className={`section-title-chevron ${showSkills ? 'open' : ''}`}>
            <ChevronRightIcon size={12} />
          </span>
          <SkillIcon size={14} className="section-title-icon" /> Skills
          {state.activeSkills.length > 0 && ` (${state.activeSkills.length})`}
        </h3>
        <div className={`sidebar-collapsible ${showSkills ? 'open' : ''}`}>
          <div className="sidebar-collapsible-inner">
            {state.skills.map((s) => (
              <div
                key={s.name}
                className={`sidebar-item ${state.activeSkills.includes(s.name) ? 'active' : ''}`}
                onClick={() => handleSkillToggle(s.name)}
              >
                <span className="item-bullet">
                  <SkillIcon size={14} />
                </span>
                <span className="item-name">{s.name}</span>
                {s.triggers && s.triggers.length > 0 && (
                  <span className="item-trigger">{s.triggers.slice(0, 2).join(', ')}</span>
                )}
              </div>
            ))}
            {state.skills.length === 0 && <div className="sidebar-empty">No skills loaded</div>}
          </div>
        </div>
      </div>

      {/* ── MCP Servers ── */}
      <div className="sidebar-section">
        <h3
          className="section-title section-title-clickable"
          onClick={() => setShowMcp(!showMcp)}
        >
          <span className={`section-title-chevron ${showMcp ? 'open' : ''}`}>
            <ChevronRightIcon size={12} />
          </span>
          <MCPIcon size={14} className="section-title-icon" /> MCP Servers ({state.mcpConnected}/{state.mcpTotal})
        </h3>
        <div className={`sidebar-collapsible ${showMcp ? 'open' : ''}`}>
          <div className="sidebar-collapsible-inner">
            {state.mcpServers.map((s) => (
              <div key={s} className="sidebar-item">
                <span className="item-bullet">
                  <MCPIcon size={14} />
                </span>
                <span className="item-name">{s}</span>
              </div>
            ))}
            {state.mcpServers.length === 0 && <div className="sidebar-empty">No MCP servers</div>}
            {state.mcpTotal > 0 && (
              <div className="sidebar-mcp-actions">
                <button
                  className="sidebar-btn sidebar-btn-connect"
                  onClick={() => api.connectMcp().then(d => {
                    if (d.ok) { api.getMcp().then(data => dispatch({ type: 'SET_MCP', payload: data })); }
                  })}
                >
                  Connect
                </button>
                <button
                  className="sidebar-btn sidebar-btn-disconnect"
                  onClick={() => api.disconnectMcp().then(d => {
                    if (d.ok) { api.getMcp().then(data => dispatch({ type: 'SET_MCP', payload: data })); }
                  })}
                >
                  Disconnect
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Sessions ── */}
      <div className="sidebar-section">
        <h3
          className="section-title section-title-clickable"
          onClick={() => setShowSessions(!showSessions)}
        >
          <span className={`section-title-chevron ${showSessions ? 'open' : ''}`}>
            <ChevronRightIcon size={12} />
          </span>
          <HistoryIcon size={14} className="section-title-icon" /> Sessions
        </h3>
        <div className={`sidebar-collapsible ${showSessions ? 'open' : ''}`}>
          <div className="sidebar-collapsible-inner">
            <div className="sidebar-session-list">
              <button className="sidebar-new-session-btn" onClick={handleNewSession}>
                + New Session
              </button>
              {sessions.length === 0 && <div className="sidebar-empty">No sessions yet</div>}
              {sessions.slice(0, 15).map((s) => (
                <div
                  key={s.id}
                  className={`sidebar-session-item ${s.id === state.currentSessionId ? 'active' : ''}`}
                >
                  <span
                    className="sidebar-session-name"
                    onClick={() => handleSwitchSession(s.id)}
                  >
                    {state.currentSessionId === s.id && <span className="session-active-dot" />}
                    {s.name}
                  </span>
                  <span className="sidebar-session-time">{formatTime(s.updated_at)}</span>
                  <span className="sidebar-session-delete" onClick={() => handleDeleteSession(s.id)}>
                    <CloseIcon size={10} />
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Memory ── */}
      <div className="sidebar-section">
        <h3
          className="section-title section-title-clickable"
          onClick={() => setShowMemory(!showMemory)}
        >
          <span className={`section-title-chevron ${showMemory ? 'open' : ''}`}>
            <ChevronRightIcon size={12} />
          </span>
          <HistoryIcon size={14} className="section-title-icon" /> Memory
        </h3>
        <div className={`sidebar-collapsible ${showMemory ? 'open' : ''}`}>
          <div className="sidebar-collapsible-inner">
            <div className="sidebar-memory">
              <div className="sidebar-memory-search">
                <input
                  className="sidebar-memory-input"
                  type="text"
                  placeholder="Search memories..."
                  value={memoryQuery}
                  onChange={(e) => setMemoryQuery(e.target.value)}
                />
                <span className="sidebar-memory-action">
                  {memorySearching ? (
                    <span className="sidebar-memory-spinner" />
                  ) : memoryQuery ? (
                    <button className="sidebar-memory-clear" onClick={handleCancelSearch} tabIndex={-1}>
                      <CloseIcon size={10} />
                    </button>
                  ) : null}
                </span>
              </div>
              {memoryError && (
                <div className="sidebar-memory-error">{memoryError}</div>
              )}
              {memoryQuery.trim() && memoryResults.length === 0 && !memorySearching && !memoryError && (
                <div className="sidebar-empty">No memories found</div>
              )}
              {memoryResults.map((m) => (
                <div key={m.id} className="sidebar-memory-item">
                  <span className="sidebar-memory-content">{m.content}</span>
                  <span className="sidebar-memory-time">
                    {m.created_at ? new Date(m.created_at).toLocaleDateString() : ''}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Knowledge ── */}
      <div className="sidebar-section">
        <h3
          className="section-title section-title-clickable"
          onClick={() => setShowKnowledge(!showKnowledge)}
        >
          <span className={`section-title-chevron ${showKnowledge ? 'open' : ''}`}>
            <ChevronRightIcon size={12} />
          </span>
          <DocumentIcon size={14} className="section-title-icon" /> Knowledge
          {state.ragDocuments.length > 0 && ` (${state.selectedKnowledgeSources.length}/${state.ragDocuments.length})`}
        </h3>
        <div className={`sidebar-collapsible ${showKnowledge ? 'open' : ''}`}>
          <div className="sidebar-collapsible-inner">
            <div className="sidebar-knowledge">
              {state.ragEnabled ? (
                <>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".txt,.md"
                    style={{ display: 'none' }}
                    onChange={handleFileUpload}
                  />
                  <button
                    className="sidebar-new-session-btn"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploading}
                  >
                    {uploading ? 'Uploading...' : '+ Upload Document'}
                  </button>
                  {uploadError && (
                    <div className="sidebar-memory-error">{uploadError}</div>
                  )}
                  {state.ragDocuments.length === 0 && (
                    <div className="sidebar-empty">No documents uploaded</div>
                  )}
                  {state.ragDocuments.map((doc, i) => {
                    const isSelected = state.selectedKnowledgeSources.includes(doc.path);
                    return (
                      <div
                        key={doc.path || i}
                        className={`sidebar-item ${isSelected ? 'active' : ''}`}
                        onClick={() => handleToggleKnowledgeSource(doc.path)}
                      >
                        <span className="item-bullet">
                          {isSelected ? <CheckIcon size={14} /> : <DocumentIcon size={14} />}
                        </span>
                        <span className="item-name">{doc.filename}</span>
                        <span className="item-provider">{doc.chunks} chunks</span>
                        <span className="sidebar-session-delete" onClick={(e) => { e.stopPropagation(); handleDeleteDoc(doc.path); }}>
                          <CloseIcon size={10} />
                        </span>
                      </div>
                    );
                  })}
                </>
              ) : (
                <div className="sidebar-empty">RAG disabled (set DASHSCOPE_API_KEY)</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── Shortcuts ── */}
      <div className="sidebar-section">
        <h3
          className="section-title section-title-clickable"
          onClick={() => setShowShortcuts(!showShortcuts)}
        >
          <span className={`section-title-chevron ${showShortcuts ? 'open' : ''}`}>
            <ChevronRightIcon size={12} />
          </span>
          Shortcuts
        </h3>
        <div className={`sidebar-collapsible ${showShortcuts ? 'open' : ''}`}>
          <div className="sidebar-collapsible-inner">
            <div className="sidebar-shortcuts">
              <div><kbd>Ctrl+B</kbd> Toggle sidebar</div>
              <div><kbd>Ctrl+L</kbd> Clear chat</div>
              <div><kbd>Enter</kbd> Send message</div>
              <div><kbd>Shift</kbd> + <kbd>Enter</kbd> New line</div>
              <div><kbd>/</kbd> Command mode</div>
            </div>
          </div>
        </div>
      </div>
      </div>

      {confirmDelete && (
        <div className="sidebar-confirm">
          <span className="sidebar-confirm-text">
            Delete {confirmDelete.type === 'session' ? 'session' : 'document'}?
          </span>
          <button className="sidebar-confirm-btn sidebar-confirm-yes" onClick={handleConfirmDelete}>
            Delete
          </button>
          <button className="sidebar-confirm-btn sidebar-confirm-no" onClick={handleCancelDelete}>
            Cancel
          </button>
        </div>
      )}

    </aside>
  );
}
