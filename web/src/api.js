const BASE = '';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    let errMsg;
    try {
      const err = await res.json();
      errMsg = err.error || err.detail || res.statusText;
    } catch {
      errMsg = res.statusText;
    }
    throw new Error(errMsg);
  }
  return res.json();
}

export const api = {
  getModels: () => request('/api/models'),
  useModel: (name) => request('/api/models/use', { method: 'POST', body: JSON.stringify({ name }) }),
  getSkills: () => request('/api/skills'),
  loadSkill: (name) => request('/api/skills/load', { method: 'POST', body: JSON.stringify({ name }) }),
  toggleSkill: (name, enabled) => request('/api/skills/toggle', { method: 'POST', body: JSON.stringify({ name, enabled }) }),
  getMcp: () => request('/api/mcp'),
  connectMcp: () => request('/api/mcp/connect', { method: 'POST' }),
  disconnectMcp: () => request('/api/mcp/disconnect', { method: 'POST' }),
  getConfig: () => request('/api/config'),
  setTheme: (theme) => request('/api/config/theme', { method: 'POST', body: JSON.stringify({ theme }) }),
  getStatus: () => request('/api/status'),

  getSessions: () => request('/api/sessions'),
  createSession: (name) => request('/api/sessions', { method: 'POST', body: JSON.stringify({ name }) }),
  renameSession: (id, name) => request(`/api/sessions/${id}`, { method: 'PATCH', body: JSON.stringify({ name }) }),
  deleteSession: (id) => request(`/api/sessions/${id}`, { method: 'DELETE' }),
  getSessionMessages: (id) => request(`/api/sessions/${id}/messages`),
  searchMemory: (q, limit = 10, sessionId = '') => {
    let url = `/api/memory/search?q=${encodeURIComponent(q)}&limit=${limit}`;
    if (sessionId) url += `&session_id=${encodeURIComponent(sessionId)}`;
    return request(url);
  },
  getMemoryStats: () => request('/api/memory/stats'),
  saveMemory: (content) => request('/api/memory/save', { method: 'POST', body: JSON.stringify({ content }) }),
  clearMemory: () => request('/api/memory/clear', { method: 'POST' }),
  getRagDocuments: () => request('/api/rag/documents'),
  getRagStatus: () => request('/api/rag/status'),
  uploadRagDocument: async (file) => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch('/api/rag/upload', { method: 'POST', body: form });
    if (!res.ok) throw new Error((await res.json()).error || 'Upload failed');
    return res.json();
  },
  deleteRagDocument: (sourcePath) => request('/api/rag/documents/delete', { method: 'POST', body: JSON.stringify({ source_path: sourcePath }) }),

  chatStream(message, { onEvent, onError, onDone, sessionId }) {
    const controller = new AbortController();

    fetch(`${BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId || '' }),
      signal: controller.signal,
    }).then(async (response) => {
      if (!response.ok) {
        onError(new Error(`HTTP ${response.status}`));
        return;
      }
      const reader = response.body.getReader();
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
              } catch (e) { /* skip malformed */ }
              eventType = '';
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
      onDone();
    }).catch((err) => {
      if (err.name !== 'AbortError') onError(err);
    });

    return controller;
  },
};