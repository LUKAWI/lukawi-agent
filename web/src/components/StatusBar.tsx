import React, { useRef } from 'react';
import { useApp } from '../context/AppContext';
import { useGSAP, gsap, getDuration } from '../lib/gsap';

export default function StatusBar() {
  const { state } = useApp();
  const mcpOk = state.mcpConnected === state.mcpTotal && state.mcpTotal > 0;

  const statusRef = useRef<HTMLDivElement>(null);
  const prevTokensRef = useRef<number>(0);
  const prevMcpOkRef = useRef<boolean | null>(null);

  useGSAP(() => {
    const tokenEl = statusRef.current?.querySelector('.token-count');
    if (!tokenEl) return;

    if (prevTokensRef.current > 0 && state.statusTokens !== prevTokensRef.current) {
      gsap.fromTo(
        tokenEl,
        { scale: 1.2, color: 'var(--accent)' },
        { scale: 1, color: 'var(--text-tertiary)', duration: getDuration(0.4), ease: 'power2.out' }
      );
    }
    prevTokensRef.current = state.statusTokens;
  }, { dependencies: [state.statusTokens], scope: statusRef });

  useGSAP(() => {
    const dot = statusRef.current?.querySelector('.mcp-dot');
    if (!dot) return;

    if (prevMcpOkRef.current !== null && prevMcpOkRef.current !== mcpOk) {
      gsap.to(dot, {
        scale: mcpOk ? 1 : 0.8,
        backgroundColor: mcpOk ? 'var(--success)' : 'var(--text-tertiary)',
        duration: getDuration(0.3),
      });
    }
    prevMcpOkRef.current = mcpOk;
  }, { dependencies: [mcpOk], scope: statusRef });

  return (
    <div
      ref={statusRef}
      className="flex items-center h-7 px-3 gap-3 shrink-0 border-t border-[var(--border)] bg-[var(--surface)] text-[11px] text-[var(--text-tertiary)] font-medium"
    >
      <span>Model: {state.currentModel || 'none'}</span>
      <span>
        Tokens: <span className="token-count">{state.statusTokens}</span>
      </span>
      <span className="flex items-center gap-1">
        <span
          className={`mcp-dot inline-block w-[6px] h-[6px] rounded-full ${
            mcpOk ? 'bg-[var(--success)]' : 'bg-[var(--text-tertiary)]'
          }`}
        />
        MCP: {state.mcpConnected}/{state.mcpTotal}
      </span>
      <span>Skills: {state.activeSkills.length} active</span>
    </div>
  );
}
