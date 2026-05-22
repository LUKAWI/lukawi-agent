import React from 'react';
import './StatusBar.css';
import CheckIcon from './icons/CheckIcon';
import ErrorIcon from './icons/ErrorIcon';

export default function StatusBar({ model, tokens, mcpConnected, mcpTotal, activeSkills }) {
  const mcpOk = mcpConnected === mcpTotal && mcpTotal > 0;

  return (
    <div className="status-bar">
      <span className="status-item">Model: {model || 'none'}</span>
      <span className="status-item">Tokens: {tokens}</span>
      <span className="status-item">
        <span className={`status-mcp-dot ${mcpOk ? 'connected' : 'disconnected'}`}>
          {mcpOk ? <CheckIcon size={12} /> : <ErrorIcon size={12} />}
        </span>
        MCP: {mcpConnected}/{mcpTotal}
      </span>
      <span className="status-item">Skills: {activeSkills} active</span>
    </div>
  );
}
