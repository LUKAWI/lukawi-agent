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
  theme: 'dark',
  sidebarVisible: true,
  statusTokens: 0,
  sessions: [],
  currentSessionId: null,
  ragDocuments: [],
  ragEnabled: false,
};

function reducer(state, action) {
  switch (action.type) {
    case 'ADD_USER_MESSAGE':
      return { ...state, messages: [...state.messages, action.payload] };
    case 'START_STREAMING': {
      const msg = { id: action.payload.id, role: 'assistant', content: '', toolCalls: [], timestamp: Date.now() };
      return { ...state, messages: [...state.messages, msg], streamingId: msg.id, isLoading: true };
    }
    case 'APPEND_TOKEN': {
      if (!state.streamingId) return state;
      return {
        ...state,
        messages: state.messages.map(m =>
          m.id === state.streamingId ? { ...m, content: m.content + action.payload } : m
        ),
      };
    }
    case 'SET_TOOL_CALL': {
      if (!state.streamingId) return state;
      const tc = { id: crypto.randomUUID(), tool: action.payload.tool, params: action.payload.params, status: 'running', result: '' };
      return {
        ...state,
        messages: state.messages.map(m =>
          m.id === state.streamingId ? { ...m, toolCalls: [...m.toolCalls, tc] } : m
        ),
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
          if (m.id !== state.streamingId || m.toolCalls.length === 0) return m;
          const tcs = [...m.toolCalls];
          tcs[tcs.length - 1] = { ...tcs[tcs.length - 1], status: action.payload.status || 'success', result: resultStr };
          return { ...m, toolCalls: tcs };
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
    case 'SET_MCP':
      return { ...state, mcpServers: action.payload.servers, mcpConnected: action.payload.connected, mcpTotal: action.payload.total };
    case 'SET_THEME':
      return { ...state, theme: action.payload };
    case 'TOGGLE_SIDEBAR':
      return { ...state, sidebarVisible: !state.sidebarVisible };
    case 'CLEAR_MESSAGES':
      return { ...state, messages: [], streamingId: null };
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