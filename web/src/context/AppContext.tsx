import React, { createContext, useContext, useReducer, useCallback } from 'react';
import type { AppState, AppAction, ChatMessage, ToolCallBlock } from '../types';

const AppContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
} | null>(null);

const initialState: AppState = {
  messages: [],
  streamingId: null,
  isLoading: false,
  isThinking: false,
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
  detailPanelOpen: false,
};

function reducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'ADD_USER_MESSAGE':
      return { ...state, messages: [...state.messages, action.payload] };

    case 'START_STREAMING': {
      const msg: ChatMessage = {
        id: action.payload.id,
        role: 'assistant',
        blocks: [],
        timestamp: Date.now(),
      };
      return { ...state, messages: [...state.messages, msg], streamingId: msg.id, isLoading: true };
    }

    case 'APPEND_TOKEN': {
      if (!state.streamingId) return state;
      return {
        ...state,
        isThinking: false,
        messages: state.messages.map((m) => {
          if (m.id !== state.streamingId) return m;
          const blocks = [...(m.blocks || [])];
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
      return {
        ...state,
        messages: state.messages.map((m) => {
          if (m.id !== state.streamingId) return m;
          return { ...m, blocks: [...(m.blocks || []), action.payload] };
        }),
      };
    }

    case 'UPDATE_TOOL_RESULT': {
      if (!state.streamingId) return state;
      return {
        ...state,
        messages: state.messages.map((m) => {
          if (m.id !== state.streamingId) return m;
          const blocks = [...(m.blocks || [])];
          for (let i = blocks.length - 1; i >= 0; i--) {
            if (blocks[i].type === 'tool' && (blocks[i] as ToolCallBlock).status === 'running') {
              blocks[i] = {
                ...blocks[i],
                status: action.payload.status === 'success' ? 'success' : 'error',
                result: action.payload.result,
              } as ToolCallBlock;
              break;
            }
          }
          return { ...m, blocks };
        }),
      };
    }

    case 'FINISH_STREAMING':
      return { ...state, streamingId: null, isLoading: false, isThinking: false };

    case 'SET_THINKING':
      return { ...state, isThinking: action.payload };

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
        return { ...state, activeSkills: state.activeSkills.filter((n) => n !== name) };
      }
      return { ...state, activeSkills: [...state.activeSkills, name] };
    }

    case 'SET_MCP':
      return { ...state, mcpServers: action.payload.servers, mcpConnected: action.payload.connected, mcpTotal: action.payload.total };

    case 'SET_THEME':
      return { ...state, theme: action.payload };

    case 'TOGGLE_SIDEBAR':
      return { ...state, sidebarVisible: !state.sidebarVisible };

    case 'TOGGLE_DETAIL_PANEL':
      return { ...state, detailPanelOpen: !state.detailPanelOpen };

    case 'CLEAR_MESSAGES':
      return { ...state, messages: [], streamingId: null, currentSessionId: null };

    case 'SET_MESSAGES':
      return { ...state, messages: action.payload, streamingId: null };

    case 'SET_SESSIONS':
      return { ...state, sessions: action.payload };

    case 'SET_CURRENT_SESSION':
      return { ...state, currentSessionId: action.payload };

    case 'SET_RAG_DOCUMENTS':
      return { ...state, ragDocuments: action.payload.documents, ragEnabled: action.payload.enabled };

    case 'TOGGLE_KNOWLEDGE_SOURCE': {
      const src = action.payload;
      const selected = state.selectedKnowledgeSources.includes(src)
        ? state.selectedKnowledgeSources.filter((s) => s !== src)
        : [...state.selectedKnowledgeSources, src];
      return { ...state, selectedKnowledgeSources: selected };
    }

    case 'SET_STATUS':
      return { ...state, ...action.payload };

    default:
      return state;
  }
}

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const stableDispatch = useCallback((action: AppAction) => dispatch(action), []);
  return <AppContext.Provider value={{ state, dispatch: stableDispatch }}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}
