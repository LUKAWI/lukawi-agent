import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api';
import {
  ModelIcon,
  SkillIcon,
  MCPIcon,
  HistoryIcon,
  DocumentIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  CloseIcon,
} from './icons';
import './Sidebar.css';

export default function Sidebar() {
  const { state, dispatch } = useApp();
  const [showShortcuts, setShowShortcuts] = useState(true);
  const [showSessions, setShowSessions] = useState(false);
  const [showKnowledge, setShowKnowledge] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    api.getModels().then(data => dispatch({ type: 'SET_MODELS', payload: data })).catch(() => {});
    api.getSkills().then(data => dispatch({ type: 'SET_SKILLS', payload: data.skills })).catch(() => {});
    api.getMcp().then(data => dispatch({ type: 'SET_MCP', payload: data })).catch(() => {});
  }, [dispatch]);

  useEffect(() => {
    api.getSessions().then(data => setSessions(data.sessions || [])).catch(() => {});
    api.getRagDocuments().then(data => dispatch({ type: 'SET_RAG_DOCUMENTS', payload: data })).catch(() => {});
  }, [dispatch]);

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

  const handleSkillLoad = async (name) => {
    try {
      await api.loadSkill(name);
      dispatch({ type: 'SET_ACTIVE_SKILLS', payload: [...state.activeSkills, name] });
    } catch (e) {
      console.error('Failed to load skill:', e);
    }
  };

  const handleNewSession = async () => {
    try {
      const s = await api.createSession('新对话');
      setSessions(prev => [s, ...prev]);
    } catch (e) {
      console.error('Failed to create session:', e);
    }
  };

  const handleDeleteSession = async (id) => {
    try {
      await api.deleteSession(id);
      setSessions(prev => prev.filter(s => s.id !== id));
    } catch (e) {
      console.error('Failed to delete session:', e);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await api.uploadRagDocument(file);
      refreshDocs();
    } catch (err) {
      console.error('Upload failed:', err);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDeleteDoc = async (sourcePath) => {
    try {
      await api.deleteRagDocument(sourcePath);
      refreshDocs();
    } catch (e) {
      console.error('Failed to delete doc:', e);
    }
  };

  const formatTime = (ts) => {
    if (!ts) return '';
    const d = new Date(ts);
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
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
            <span className="item-name">{m.name}</span>
            <span className="item-provider">{m.model || m.provider}</span>
          </div>
        ))}
        {state.models.length === 0 && <div className="sidebar-empty">No models available</div>}
      </div>

      <div className="sidebar-section">
        <h3 className="section-title">
          <SkillIcon size={14} className="section-title-icon" />
          Skills {state.activeSkills.length > 0 && `(${state.activeSkills.length})`}
        </h3>
        {state.skills.map((s) => (
          <div
            key={s.name}
            className={`sidebar-item ${state.activeSkills.includes(s.name) ? 'active' : ''}`}
            onClick={() => handleSkillLoad(s.name)}
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

      <div className="sidebar-section">
        <h3 className="section-title">
          <MCPIcon size={14} className="section-title-icon" />
          MCP Servers ({state.mcpConnected}/{state.mcpTotal})
        </h3>
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

      <div className="sidebar-section">
        <h3
          className="section-title section-title-clickable"
          onClick={() => setShowSessions(!showSessions)}
        >
          {showSessions ? <ChevronDownIcon size={12} /> : <ChevronRightIcon size={12} />}
          <HistoryIcon size={14} className="section-title-icon" /> Sessions
        </h3>
        {showSessions && (
          <div className="sidebar-session-list">
            <button className="sidebar-new-session-btn" onClick={handleNewSession}>
              + New Session
            </button>
            {sessions.length === 0 && <div className="sidebar-empty">No sessions yet</div>}
            {sessions.slice(0, 15).map((s) => (
              <div key={s.id} className="sidebar-session-item">
                <span
                  className="sidebar-session-name"
                  onClick={() => console.log('switch session', s.id)}
                >
                  {s.name}
                </span>
                <span className="sidebar-session-time">{formatTime(s.updated_at)}</span>
                <span className="sidebar-session-delete" onClick={() => handleDeleteSession(s.id)}>
                  <CloseIcon size={10} />
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="sidebar-section">
        <h3
          className="section-title section-title-clickable"
          onClick={() => setShowKnowledge(!showKnowledge)}
        >
          {showKnowledge ? <ChevronDownIcon size={12} /> : <ChevronRightIcon size={12} />}
          <DocumentIcon size={14} className="section-title-icon" /> Knowledge
          {state.ragDocuments.length > 0 && ` (${state.ragDocuments.length})`}
        </h3>
        {showKnowledge && (
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
                {state.ragDocuments.length === 0 && (
                  <div className="sidebar-empty">No documents uploaded</div>
                )}
                {state.ragDocuments.map((doc, i) => (
                  <div key={doc.path || i} className="sidebar-session-item">
                    <span className="sidebar-session-name">
                      <DocumentIcon size={12} className="item-bullet" />
                      {doc.filename}
                    </span>
                    <span className="sidebar-session-time">{doc.chunks} chunks</span>
                    <span className="sidebar-session-delete" onClick={() => handleDeleteDoc(doc.path)}>
                      <CloseIcon size={10} />
                    </span>
                  </div>
                ))}
              </>
            ) : (
              <div className="sidebar-empty">RAG disabled (set DASHSCOPE_API_KEY)</div>
            )}
          </div>
        )}
      </div>

      <div className="sidebar-section">
        <h3
          className="section-title section-title-clickable"
          onClick={() => setShowShortcuts(!showShortcuts)}
        >
          {showShortcuts ? <ChevronDownIcon size={12} /> : <ChevronRightIcon size={12} />}
          Shortcuts
        </h3>
        {showShortcuts && (
          <div className="sidebar-shortcuts">
            <div><kbd>Ctrl+B</kbd> Toggle sidebar</div>
            <div><kbd>Ctrl+L</kbd> Clear chat</div>
          </div>
        )}
      </div>
      </div>
    </aside>
  );
}
