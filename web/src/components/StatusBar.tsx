import React from 'react';
import { useApp } from '../context/AppContext';

export default function StatusBar() {
  const { state } = useApp();
  const mcpOk = state.mcpConnected === state.mcpTotal && state.mcpTotal > 0;

  return (
    <div className="flex items-center h-7 px-3 gap-3 shrink-0 border-t border-[var(--border)] bg-[var(--surface)] text-[11px] text-[var(--text-tertiary)] font-medium">
      <span>Model: {state.currentModel || 'none'}</span>
      <span>Tokens: {state.statusTokens}</span>
      <span className="flex items-center gap-1">
        <span
          className={`inline-block w-[6px] h-[6px] rounded-full ${
            mcpOk ? 'bg-[var(--success)]' : 'bg-[var(--text-tertiary)]'
          }`}
        />
        MCP: {state.mcpConnected}/{state.mcpTotal}
      </span>
      <span>Skills: {state.activeSkills.length} active</span>
    </div>
  );
}
