import { cn } from '../../lib/utils';
import type { SessionData } from '../../types';
import { Plus, Trash2, History } from 'lucide-react';
import { Section } from './Section';

export interface SessionListProps {
  sessions: SessionData[];
  currentSessionId: string | null;
  editingSession: string | null;
  editName: string;
  onNewSession: () => void;
  onSwitchSession: (id: string) => void;
  onRename: (id: string) => void;
  onDelete: (id: string) => void;
  onSetEditingSession: (id: string | null) => void;
  onSetEditName: (name: string) => void;
}

function formatTime(ts: string) {
  if (!ts) return '';
  const d = new Date(ts);
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
}

export function SessionList({
  sessions,
  currentSessionId,
  editingSession,
  editName,
  onNewSession,
  onSwitchSession,
  onRename,
  onDelete,
  onSetEditingSession,
  onSetEditName,
}: SessionListProps) {
  return (
    <Section title="Sessions" icon={<History size={14} />} defaultOpen variant="highlighted" badge={sessions.length}>
      <button
        className="flex items-center gap-1.5 w-full px-2.5 py-1.5 mb-1 text-[12px] font-semibold rounded-[6px] border-2 border-dashed border-[var(--border)] text-[var(--accent)] hover:bg-[var(--accent-light)] hover:border-[var(--accent)] transition-colors"
        onClick={onNewSession}
      >
        <Plus size={14} />
        New Session
      </button>
      <div className="max-h-[200px] overflow-y-auto space-y-0.5">
        {sessions.map((s) => (
          <div
            key={s.id}
            className={cn(
              'flex items-center gap-1.5 px-2 py-1 rounded-[6px] text-[12px] border-l-2 border-transparent transition-colors',
              s.id === currentSessionId
                ? 'bg-[var(--accent-light)] border-l-[var(--accent)]'
                : 'hover:bg-[var(--surface-alt)]',
            )}
          >
            {editingSession === s.id ? (
              <input
                className="flex-1 bg-[var(--bg)] border border-[var(--border)] rounded px-1.5 py-0.5 text-[12px] text-[var(--text)] outline-none"
                value={editName}
                onChange={(e) => onSetEditName(e.target.value)}
                onBlur={() => onRename(s.id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') onRename(s.id);
                  if (e.key === 'Escape') onSetEditingSession(null);
                }}
                autoFocus
              />
            ) : (
              <span
                className="flex-1 truncate cursor-pointer hover:text-[var(--accent)] transition-colors"
                onClick={() => onSwitchSession(s.id)}
                onDoubleClick={() => {
                  onSetEditingSession(s.id);
                  onSetEditName(s.name);
                }}
              >
                {s.name}
              </span>
            )}
            <span className="text-[10px] text-[var(--text-tertiary)] shrink-0">
              {formatTime(s.updated_at || s.created_at)}
            </span>
            <button
              className="opacity-0 hover:opacity-100 text-[var(--text-tertiary)] hover:text-[var(--error)] transition-all"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(s.id);
              }}
            >
              <Trash2 size={12} />
            </button>
          </div>
        ))}
      </div>
    </Section>
  );
}
