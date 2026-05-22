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
  getMcp: () => request('/api/mcp'),
  connectMcp: () => request('/api/mcp/connect', { method: 'POST' }),
  disconnectMcp: () => request('/api/mcp/disconnect', { method: 'POST' }),
  getConfig: () => request('/api/config'),
  setTheme: (theme) => request('/api/config/theme', { method: 'POST', body: JSON.stringify({ theme }) }),
  getStatus: () => request('/api/status'),

  chatStream(message, { onEvent, onError, onDone }) {
    const controller = new AbortController();

    fetch(`${BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
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