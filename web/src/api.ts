import type { ModelInfo, SkillInfo, McpStatus, SessionData, MessageData, MemoryItem, RagDocument, StatusData } from './types';

const BASE = '';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    let msg: string;
    try {
      const err = await res.json();
      msg = err.error || err.detail || res.statusText;
    } catch {
      msg = res.statusText;
    }
    throw new Error(msg);
  }
  return res.json();
}

export const api = {
  getModels: () => request<{ models: ModelInfo[]; current: string }>('/api/models'),
  useModel: (name: string) => request('/api/models/use', { method: 'POST', body: JSON.stringify({ name }) }),

  getSkills: () => request<{ skills: SkillInfo[] }>('/api/skills'),
  toggleSkill: (name: string, enabled: boolean) =>
    request('/api/skills/toggle', { method: 'POST', body: JSON.stringify({ name, enabled }) }),

  getMcp: () => request<McpStatus>('/api/mcp'),
  connectMcp: () => request<{ ok: boolean }>('/api/mcp/connect', { method: 'POST' }),
  disconnectMcp: () => request<{ ok: boolean }>('/api/mcp/disconnect', { method: 'POST' }),

  getConfig: () => request<{ theme?: string }>('/api/config'),
  setTheme: (theme: string) => request('/api/config/theme', { method: 'POST', body: JSON.stringify({ theme }) }),

  getStatus: () => request<StatusData>('/api/status'),

  getSessions: () => request<{ sessions: SessionData[] }>('/api/sessions'),
  createSession: (name: string) => request<SessionData>('/api/sessions', { method: 'POST', body: JSON.stringify({ name }) }),
  renameSession: (id: string, name: string) =>
    request(`/api/sessions/${id}`, { method: 'PATCH', body: JSON.stringify({ name }) }),
  deleteSession: (id: string) => request(`/api/sessions/${id}`, { method: 'DELETE' }),
  getSessionMessages: (id: string) => request<{ messages: MessageData[] }>(`/api/sessions/${id}/messages`),

  searchMemory: (q: string, limit = 10, sessionId = '') => {
    let url = `/api/memory/search?q=${encodeURIComponent(q)}&limit=${limit}`;
    if (sessionId) url += `&session_id=${encodeURIComponent(sessionId)}`;
    return request<{ memories: MemoryItem[] }>(url);
  },
  saveMemory: (content: string) => request('/api/memory/save', { method: 'POST', body: JSON.stringify({ content }) }),
  clearMemory: () => request('/api/memory/clear', { method: 'POST' }),

  getRagDocuments: () => request<{ documents: RagDocument[]; enabled: boolean }>('/api/rag/documents'),
  uploadRagDocument: async (file: File) => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch('/api/rag/upload', { method: 'POST', body: form });
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).error || 'Upload failed');
    return res.json();
  },
  deleteRagDocument: (sourcePath: string) =>
    request('/api/rag/documents/delete', { method: 'POST', body: JSON.stringify({ source_path: sourcePath }) }),

  chatStream(
    message: string,
    {
      onEvent,
      onError,
      onDone,
      sessionId,
      knowledgeSources,
    }: {
      onEvent: (eventType: string, data: Record<string, unknown>) => void;
      onError: (err: Error) => void;
      onDone: () => void;
      sessionId: string | null;
      knowledgeSources?: string[];
    },
  ) {
    const controller = new AbortController();

    fetch(`${BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId || '', knowledge_sources: knowledgeSources || [] }),
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          onError(new Error(`HTTP ${response.status}`));
          return;
        }
        const reader = response.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let eventType = '';

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (line.startsWith('event: ')) {
                eventType = line.slice(7).trim();
              } else if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));
                  onEvent(eventType, data);
                } catch {
                  /* skip malformed */
                }
                eventType = '';
              }
            }
          }
        } finally {
          reader.releaseLock();
        }
        onDone();
      })
      .catch((err) => {
        if (err.name !== 'AbortError') onError(err);
      });

    return controller;
  },
};
