import React, { useState, useRef, useEffect, useCallback } from 'react';
import { cn } from '../lib/utils';
import { useApp } from '../context/AppContext';
import { api } from '../api';
import type { SessionData, RagDocument, MemoryItem, SkillInfo } from '../types';
import {
  ChevronRight,
  Plus,
  Trash2,
  Search,
  X,
  Upload,
  Check,
  FileText,
  Cpu,
  Puzzle,
  Server,
  History,
  Brain,
  BookOpen,
} from 'lucide-react';

interface SectionProps {
  title: string;
  icon: React.ReactNode;
  defaultOpen?: boolean;
  badge?: string | number;
  children: React.ReactNode;
}

function Section({ title, icon, defaultOpen = false, badge, children }: SectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="mb-1">
      <button
        className="flex items-center gap-1.5 w-full px-2 py-1.5 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--text-tertiary)] rounded-[6px] hover:text-[var(--text-secondary)] hover:bg-[var(--surface-alt)] transition-colors"
        onClick={() => setOpen(!open)}
      >
        <ChevronRight
          size={12}
          className={cn('transition-transform duration-200', open && 'rotate-90')}
        />
        <span className="opacity-70 shrink-0">{icon}</span>
        {title}
        {badge !== undefined && (
          <span className="ml-auto text-[10px] font-medium text-[var(--text-tertiary)] bg-[var(--surface-alt)] px-1.5 py-0.5 rounded-[3px]">
            {badge}
          </span>
        )}
      </button>
      <div
        className="grid transition-[grid-template-rows] duration-250 ease-out"
        style={{ gridTemplateRows: open ? '1fr' : '0fr' }}
      >
        <div className="overflow-hidden">{children}</div>
      </div>
    </div>
  );
}

export default function Sidebar() {
  const { state, dispatch } = useApp();
  const [sessions, setSessions] = useState<SessionData[]>([]);
  const [memoryQuery, setMemoryQuery] = useState('');
  const [memoryResults, setMemoryResults] = useState<MemoryItem[]>([]);
  const [memorySearching, setMemorySearching] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<{ type: string; id?: string; path?: string } | null>(null);
  const [editingSession, setEditingSession] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const searchTimerRef = useRef<ReturnType<typeof setTimeout>>();
  const searchReqRef = useRef(0);

  const loadSessions = useCallback(() => {
    api.getSessions().then((data) => setSessions(data.sessions || [])).catch(() => {});
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
    } catch {}
  }, [dispatch]);

  useEffect(() => {
    loadInitialData();
    loadSessions();
    api.getRagDocuments().then((data) => dispatch({ type: 'SET_RAG_DOCUMENTS', payload: data })).catch(() => {});
  }, []);

  // Memory search with debounce
  useEffect(() => {
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    if (!memoryQuery.trim()) {
      setMemoryResults([]);
      return;
    }
    setMemorySearching(true);
    const reqId = ++searchReqRef.current;
    searchTimerRef.current = setTimeout(async () => {
      try {
        const data = await api.searchMemory(memoryQuery, 10, state.currentSessionId ?? undefined);
        if (reqId !== searchReqRef.current) return;
        setMemoryResults(data.memories || []);
      } catch {
        if (reqId !== searchReqRef.current) return;
        setMemoryResults([]);
      }
      setMemorySearching(false);
    }, 400);
    return () => {
      if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    };
  }, [memoryQuery, state.currentSessionId]);

  const handleNewSession = async () => {
    try {
      const s = await api.createSession('新对话');
      setSessions((prev) => [s, ...prev]);
      dispatch({ type: 'CLEAR_MESSAGES' });
      dispatch({ type: 'SET_CURRENT_SESSION', payload: s.id });
    } catch {}
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
    } catch {
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
    } catch {}
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
      setUploadError((err as Error).message || 'Delete failed');
    }
    setConfirmDelete(null);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      await api.uploadRagDocument(file);
      const data = await api.getRagDocuments();
      dispatch({ type: 'SET_RAG_DOCUMENTS', payload: data });
    } catch (err) {
      setUploadError((err as Error).message || 'Upload failed');
    }
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const formatTime = (ts: string) => {
    if (!ts) return '';
    const d = new Date(ts);
    return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
  };

  return (
    <aside
      className={cn(
        'w-[260px] shrink-0 h-full flex flex-col bg-[var(--surface)] border-r border-[var(--border)] overflow-hidden transition-all duration-250',
        state.sidebarVisible ? 'opacity-100' : 'w-0 opacity-0 border-r-0',
      )}
    >
      <div className="flex-1 overflow-y-auto p-2">
        {/* Models */}
        <Section title="Models" icon={<Cpu size={14} />} defaultOpen badge={state.models.length}>
          {state.models.map((m) => (
            <div
              key={m.name}
              className={cn(
                'flex items-center gap-2 px-2.5 py-1.5 rounded-[6px] text-[13px] cursor-pointer border-l-2 border-transparent transition-colors hover:bg-[var(--surface-alt)]',
                m.name === state.currentModel && 'bg-[var(--accent-light)] border-l-[var(--accent)]',
              )}
              onClick={() => {
                api.useModel(m.name);
                dispatch({ type: 'SET_CURRENT_MODEL', payload: m.name });
              }}
            >
              <span className="text-[13px] truncate">{m.model || m.name}</span>
              <span className="ml-auto text-[11px] text-[var(--text-tertiary)] bg-[var(--surface-alt)] px-1 py-0.5 rounded-[3px]">
                {m.provider}
              </span>
            </div>
          ))}
          {state.models.length === 0 && (
            <div className="px-2.5 py-1.5 text-[12px] italic text-[var(--text-tertiary)]">No models</div>
          )}
        </Section>

        {/* Skills */}
        <Section title="Skills" icon={<Puzzle size={14} />} badge={state.activeSkills.length}>
          {state.skills.map((s) => (
            <div
              key={s.name}
              className={cn(
                'flex items-center gap-2 px-2.5 py-1.5 rounded-[6px] text-[13px] cursor-pointer border-l-2 border-transparent transition-colors',
                state.activeSkills.includes(s.name)
                  ? 'bg-[var(--accent-light)] border-l-[var(--accent)]'
                  : 'hover:bg-[var(--surface-alt)]',
              )}
              onClick={() => {
                const enabled = !state.activeSkills.includes(s.name);
                api.toggleSkill(s.name, enabled);
                dispatch({ type: 'TOGGLE_ACTIVE_SKILL', payload: s.name });
              }}
            >
              <span className="truncate">{s.name}</span>
            </div>
          ))}
          {state.skills.length === 0 && (
            <div className="px-2.5 py-1.5 text-[12px] italic text-[var(--text-tertiary)]">No skills</div>
          )}
        </Section>

        {/* MCP */}
        <Section
          title="MCP"
          icon={<Server size={14} />}
          badge={`${state.mcpConnected}/${state.mcpTotal}`}
        >
          {state.mcpServers.map((s) => (
            <div key={s} className="flex items-center gap-2 px-2.5 py-1.5 text-[13px]">
              <span className="truncate">{s}</span>
            </div>
          ))}
          {state.mcpServers.length === 0 && (
            <div className="px-2.5 py-1.5 text-[12px] italic text-[var(--text-tertiary)]">No servers</div>
          )}
          {state.mcpTotal > 0 && (
            <div className="flex gap-1.5 px-2.5 py-1.5">
              <button
                className="flex-1 px-2 py-1 text-[11px] font-medium rounded-[6px] border border-[var(--border)] bg-[var(--surface-alt)] text-[var(--text)] hover:bg-[var(--success)] hover:text-white hover:border-[var(--success)] transition-colors"
                onClick={() => api.connectMcp().then(() => api.getMcp().then((d) => dispatch({ type: 'SET_MCP', payload: d })))}
              >
                Connect
              </button>
              <button
                className="flex-1 px-2 py-1 text-[11px] font-medium rounded-[6px] border border-[var(--border)] bg-[var(--surface-alt)] text-[var(--text)] hover:bg-[var(--error)] hover:text-white hover:border-[var(--error)] transition-colors"
                onClick={() =>
                  api.disconnectMcp().then(() => api.getMcp().then((d) => dispatch({ type: 'SET_MCP', payload: d })))
                }
              >
                Disconnect
              </button>
            </div>
          )}
        </Section>

        {/* Sessions */}
        <Section title="Sessions" icon={<History size={14} />} defaultOpen badge={sessions.length}>
          <button
            className="flex items-center gap-1.5 w-full px-2.5 py-1.5 mb-1 text-[12px] font-semibold rounded-[6px] border-2 border-dashed border-[var(--border)] text-[var(--accent)] hover:bg-[var(--accent-light)] hover:border-[var(--accent)] transition-colors"
            onClick={handleNewSession}
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
                  s.id === state.currentSessionId
                    ? 'bg-[var(--accent-light)] border-l-[var(--accent)]'
                    : 'hover:bg-[var(--surface-alt)]',
                )}
              >
                {editingSession === s.id ? (
                  <input
                    className="flex-1 bg-[var(--bg)] border border-[var(--border)] rounded px-1.5 py-0.5 text-[12px] text-[var(--text)] outline-none"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    onBlur={() => handleRename(s.id)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleRename(s.id);
                      if (e.key === 'Escape') setEditingSession(null);
                    }}
                    autoFocus
                  />
                ) : (
                  <span
                    className="flex-1 truncate cursor-pointer hover:text-[var(--accent)] transition-colors"
                    onClick={() => handleSwitchSession(s.id)}
                    onDoubleClick={() => {
                      setEditingSession(s.id);
                      setEditName(s.name);
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
                    setConfirmDelete({ type: 'session', id: s.id });
                  }}
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
          </div>
        </Section>

        {/* Memory */}
        <Section title="Memory" icon={<Brain size={14} />}>
          <div className="px-2.5 py-1">
            <div className="flex items-center gap-1.5 mb-1">
              <div className="relative flex-1">
                <Search size={12} className="absolute left-2 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)]" />
                <input
                  className="w-full pl-7 pr-2 py-1.5 text-[12px] rounded-[6px] border border-[var(--border)] bg-[var(--bg)] text-[var(--text)] outline-none focus:border-[var(--accent)] focus:shadow-[0_0_0_3px_var(--accent-glow)] transition-colors"
                  placeholder="Search memory..."
                  value={memoryQuery}
                  onChange={(e) => setMemoryQuery(e.target.value)}
                />
                {memoryQuery && (
                  <button
                    className="absolute right-1.5 top-1/2 -translate-y-1/2"
                    onClick={() => setMemoryQuery('')}
                  >
                    <X size={12} className="text-[var(--text-tertiary)]" />
                  </button>
                )}
              </div>
            </div>
            {memorySearching && (
              <div className="text-[11px] text-[var(--text-tertiary)] px-1 py-1">Searching...</div>
            )}
            {memoryResults.map((mem) => (
              <div key={mem.id} className="px-1 py-1 text-[12px] border-l-2 border-transparent hover:border-l-[var(--accent)] hover:bg-[var(--surface-alt)] rounded-[4px] transition-colors">
                <span className="block truncate">{mem.content}</span>
                {mem.timestamp && (
                  <span className="text-[10px] text-[var(--text-tertiary)]">{new Date(mem.timestamp).toLocaleDateString()}</span>
                )}
              </div>
            ))}
          </div>
        </Section>

        {/* Knowledge */}
        <Section title="Knowledge" icon={<BookOpen size={14} />} badge={`${state.selectedKnowledgeSources.length}/${state.ragDocuments.length}`}>
          <div className="px-2.5 py-1">
            {state.ragEnabled ? (
              <>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".txt,.md"
                  className="hidden"
                  onChange={handleFileUpload}
                />
                <button
                  className="flex items-center justify-center gap-1.5 w-full px-2.5 py-1.5 mb-1 text-[12px] font-semibold rounded-[6px] border-2 border-dashed border-[var(--border)] text-[var(--accent)] hover:bg-[var(--accent-light)] hover:border-[var(--accent)] transition-colors disabled:opacity-50"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                >
                  <Upload size={14} />
                  {uploading ? 'Uploading...' : 'Upload'}
                </button>
                {uploadError && (
                  <div className="px-2 py-1 mb-1 text-[11px] text-[var(--error)] bg-[var(--error-light)] rounded-[6px] border-l-2 border-[var(--error)]">
                    {uploadError}
                  </div>
                )}
                {state.ragDocuments.map((doc) => (
                  <div
                    key={doc.path}
                    className={cn(
                      'flex items-center gap-2 px-2 py-1 rounded-[6px] text-[12px] cursor-pointer border-l-2 border-transparent transition-colors hover:bg-[var(--surface-alt)]',
                      state.selectedKnowledgeSources.includes(doc.path) && 'bg-[var(--accent-light)] border-l-[var(--accent)]',
                    )}
                    onClick={() => dispatch({ type: 'TOGGLE_KNOWLEDGE_SOURCE', payload: doc.path })}
                  >
                    {state.selectedKnowledgeSources.includes(doc.path) ? (
                      <Check size={12} className="text-[var(--accent)] shrink-0" />
                    ) : (
                      <FileText size={12} className="text-[var(--text-tertiary)] shrink-0" />
                    )}
                    <span className="truncate">{doc.filename}</span>
                    <span className="text-[10px] text-[var(--text-tertiary)]">{doc.chunks} chunks</span>
                    <button
                      className="ml-auto opacity-0 hover:opacity-100 text-[var(--text-tertiary)] hover:text-[var(--error)] transition-all"
                      onClick={(e) => {
                        e.stopPropagation();
                        setConfirmDelete({ type: 'knowledge', path: doc.path });
                      }}
                    >
                      <Trash2 size={10} />
                    </button>
                  </div>
                ))}
                {state.ragDocuments.length === 0 && (
                  <div className="text-[12px] italic text-[var(--text-tertiary)] px-1">No documents</div>
                )}
              </>
            ) : (
              <div className="text-[12px] italic text-[var(--text-tertiary)] px-1">RAG disabled</div>
            )}
          </div>
        </Section>
      </div>

      {/* Confirm delete bar */}
      {confirmDelete && (
        <div className="flex items-center gap-2 px-3 py-2 border-t border-[var(--border)] bg-[var(--surface)] animate-[fade-in_200ms_ease]">
          <span className="flex-1 text-[12px] font-semibold text-[var(--text)]">
            Delete {confirmDelete.type}?
          </span>
          <button className="px-2 py-1 text-[11px] font-semibold rounded-[6px] border border-[var(--border)] bg-[var(--surface-alt)] text-[var(--text)] hover:bg-[var(--error)] hover:text-white hover:border-[var(--error)] transition-colors" onClick={handleDelete}>
            Delete
          </button>
          <button className="px-2 py-1 text-[11px] font-semibold rounded-[6px] border border-[var(--border)] bg-[var(--surface-alt)] text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors" onClick={() => setConfirmDelete(null)}>
            Cancel
          </button>
        </div>
      )}
    </aside>
  );
}
