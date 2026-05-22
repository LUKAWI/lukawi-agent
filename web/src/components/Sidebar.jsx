import React, { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api';
import {
  ModelIcon,
  SkillIcon,
  MCPIcon,
  ChevronDownIcon,
  ChevronRightIcon,
} from './icons';
import './Sidebar.css';

export default function Sidebar() {
  const { state, dispatch } = useApp();
  const [showShortcuts, setShowShortcuts] = useState(true);
  const [showSessions, setShowSessions] = useState(false);

  useEffect(() => {
    api.getModels().then(data => dispatch({ type: 'SET_MODELS', payload: data })).catch(() => {});
    api.getSkills().then(data => dispatch({ type: 'SET_SKILLS', payload: data.skills })).catch(() => {});
    api.getMcp().then(data => dispatch({ type: 'SET_MCP', payload: data })).catch(() => {});
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
          onClick={() => setShowShortcuts(!showShortcuts)}
        >
          {showShortcuts ? <ChevronDownIcon size={12} /> : <ChevronRightIcon size={12} />}
          Shortcuts
        </h3>
        {showShortcuts && (
          <div className="sidebar-shortcuts">
            <div><kbd>Ctrl+B</kbd> Toggle sidebar</div>
            <div><kbd>Ctrl+L</kbd> Clear chat</div>
            <div><kbd>Ctrl+M</kbd> Switch model</div>
          </div>
        )}
      </div>
      </div>
    </aside>
  );
}
