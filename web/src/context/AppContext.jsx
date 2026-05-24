import React, { createContext, useContext, useReducer, useCallback } from 'react';

const AppContext = createContext(null);

const initialState = {
  messages: [],
  streamingId: null,
  isLoading: false,
  models: [],
  currentModel: '',
  skills: [],
  activeSkills: [],
  mcpServers: [],
  mcpConnected: 0,
  mcpTotal: 0,
  theme: 'light',
  sidebarVisible: false,
  statusTokens: 0,
  sessions: [],
  currentSessionId: null,
  ragDocuments: [],
  ragEnabled: false,
  selectedKnowledgeSources: [],
};

function reducer(state, action) {
  switch (action.type) {
    case 'ADD_USER_MESSAGE':
      return { ...state, messages: [...state.messages, action.payload] };
    case 'START_STREAMING': {
      const msg = { id: action.payload.id, role: 'assistant', blocks: [], timestamp: Date.now() };
      return { ...state, messages: [...state.messages, msg], streamingId: msg.id, isLoading: true };
    }
    case 'APPEND_TOKEN': {
      if (!state.streamingId) return state;
      return {
        ...state,
        messages: state.messages.map(m => {
          if (m.id !== state.streamingId) return m;
          const blocks = [...m.blocks];
          const last = blocks[blocks.length - 1];
          if (last && last.type === 'text') {
            blocks[blocks.length - 1] = { ...last, content: last.content + action.payload };
          } else {
            blocks.push({ type: 'text', content: action.payload });
          }
          return { ...m, blocks };
        }),
      };
    }
    case 'SET_TOOL_CALL': {
      if (!state.streamingId) return state;
      const tc = {
        type: 'tool',
        id: crypto.randomUUID(),
        tool: action.payload.tool,
        params: action.payload.params,
        status: 'running',
        result: '',
        collapsed: true,
      };
      return {
        ...state,
        messages: state.messages.map(m => {
          if (m.id !== state.streamingId) return m;
          return { ...m, blocks: [...m.blocks, tc] };
        }),
      };
    }
    case 'UPDATE_TOOL_RESULT': {
      if (!state.streamingId) return state;
      const resultStr = typeof action.payload.result === 'string'
        ? action.payload.result
        : JSON.stringify(action.payload.result, null, 2);
      return {
        ...state,
        messages: state.messages.map(m => {
          if (m.id !== state.streamingId) return m;
          const blocks = [...m.blocks];
          for (let i = blocks.length - 1; i >= 0; i--) {
            if (blocks[i].type === 'tool' && blocks[i].status === 'running') {
              blocks[i] = {
                ...blocks[i],
                status: action.payload.status === 'success' ? 'success' : 'error',
                result: resultStr,
              };
              break;
            }
          }
          return { ...m, blocks };
        }),
      };
    }
    case 'FINISH_STREAMING':
      return { ...state, streamingId: null, isLoading: false };
    case 'ADD_SYSTEM_MESSAGE':
      return { ...state, messages: [...state.messages, action.payload] };
    case 'SET_MODELS':
      return { ...state, models: action.payload.models, currentModel: action.payload.current };
    case 'SET_CURRENT_MODEL':
      return { ...state, currentModel: action.payload };
    case 'SET_SKILLS':
      return { ...state, skills: action.payload };
    case 'SET_ACTIVE_SKILLS':
      return { ...state, activeSkills: action.payload };
    case 'TOGGLE_ACTIVE_SKILL': {
      const name = action.payload;
      const idx = state.activeSkills.indexOf(name);
      if (idx >= 0) {
        return { ...state, activeSkills: state.activeSkills.filter(n => n !== name) };
      }
      return { ...state, activeSkills: [...state.activeSkills, name] };
    }
    case 'SET_MCP':
      return { ...state, mcpServers: action.payload.servers, mcpConnected: action.payload.connected, mcpTotal: action.payload.total };
    case 'SET_THEME':
      return { ...state, theme: action.payload };
    case 'TOGGLE_SIDEBAR':
      return { ...state, sidebarVisible: !state.sidebarVisible };
    case 'CLEAR_MESSAGES':
      return { ...state, messages: [], streamingId: null, currentSessionId: null };
    case 'SET_MESSAGES':
      return { ...state, messages: action.payload, streamingId: null };
    case 'SET_STATUS':
      return { ...state, ...action.payload };
    case 'SET_SESSIONS':
      return { ...state, sessions: action.payload };
    case 'SET_CURRENT_SESSION':
      return { ...state, currentSessionId: action.payload };
    case 'SET_RAG_DOCUMENTS':
      return { ...state, ragDocuments: action.payload.documents, ragEnabled: action.payload.enabled };
    case 'SET_RAG_ENABLED':
      return { ...state, ragEnabled: action.payload };
    case 'TOGGLE_KNOWLEDGE_SOURCE': {
      const src = action.payload;
      const selected = state.selectedKnowledgeSources.includes(src)
        ? state.selectedKnowledgeSources.filter(s => s !== src)
        : [...state.selectedKnowledgeSources, src];
      return { ...state, selectedKnowledgeSources: selected };
    }
    default:
      return state;
  }
}

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const stableDispatch = useCallback((action) => dispatch(action), []);
  return (
    <AppContext.Provider value={{ state, dispatch: stableDispatch }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}