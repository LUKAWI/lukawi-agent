import { Server } from 'lucide-react';
import { Section } from './Section';

export interface McpStatusProps {
  servers: string[];
  connected: number;
  total: number;
  onConnect: () => void;
  onDisconnect: () => void;
}

export function McpStatus({ servers, connected, total, onConnect, onDisconnect }: McpStatusProps) {
  return (
    <Section
      title="MCP"
      icon={<Server size={14} />}
      defaultOpen={false}
      badge={`${connected}/${total}`}
    >
      {servers.map((s) => (
        <div key={s} className="flex items-center gap-2 px-2.5 py-1.5 text-[13px]">
          <span className="truncate">{s}</span>
        </div>
      ))}
      {servers.length === 0 && (
        <div className="px-2.5 py-1.5 text-[12px] italic text-[var(--text-tertiary)]">No servers</div>
      )}
      {total > 0 && (
        <div className="flex gap-1.5 px-2.5 py-1.5">
          <button
            className="flex-1 px-2 py-1 text-[11px] font-medium rounded-[6px] border border-[var(--border)] bg-[var(--surface-alt)] text-[var(--text)] hover:bg-[var(--success)] hover:text-white hover:border-[var(--success)] transition-colors"
            onClick={onConnect}
          >
            Connect
          </button>
          <button
            className="flex-1 px-2 py-1 text-[11px] font-medium rounded-[6px] border border-[var(--border)] bg-[var(--surface-alt)] text-[var(--text)] hover:bg-[var(--error)] hover:text-white hover:border-[var(--error)] transition-colors"
            onClick={onDisconnect}
          >
            Disconnect
          </button>
        </div>
      )}
    </Section>
  );
}
