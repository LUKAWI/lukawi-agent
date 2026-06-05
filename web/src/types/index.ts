export interface ModelInfo {
  name: string;
  model: string;
  provider: string;
  display_name?: string;  // Optional display name for custom models
}

export interface SkillInfo {
  name: string;
  selected?: boolean;
  triggers?: string[];
}

export interface McpStatus {
  servers: string[];
  connected: number;
  total: number;
}

export interface SessionData {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface MessageData {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface MemoryItem {
  id: string;
  content: string;
  timestamp: string;
  score?: number;
}

export interface RagDocument {
  path: string;
  filename: string;
  chunks: number;
}

export interface StatusData {
  model?: string;
  tokens?: number;
}

export interface TextBlock {
  type: 'text';
  content: string;
}

export interface ToolCallBlock {
  type: 'tool';
  id: string;
  tool: string;
  params: Record<string, unknown>;
  status: 'running' | 'success' | 'error';
  result?: string;
  collapsed?: boolean;
}

export type MessageBlock = TextBlock | ToolCallBlock;

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content?: string;
  blocks?: MessageBlock[];
  toolCalls?: ToolCallBlock[];
  timestamp: number;
}

export interface SSEEvent {
  event: string;
  data: {
    session_id?: string;
    content?: string;
    tool?: string;
    params?: Record<string, unknown>;
    result?: string;
    status?: string;
    error?: string;
  };
}

// ── SSE Event Type Guards ──

export interface SSEThinkingEvent {
  event: 'thinking';
  data: { session_id?: string };
}

export interface SSEToolCallEvent {
  event: 'tool_call';
  data: { tool: string; params?: Record<string, unknown> };
}

export interface SSEToolResultEvent {
  event: 'tool_result';
  data: { result: unknown; status: string };
}

export interface SSEAnswerEvent {
  event: 'answer';
  data: { content: string };
}

export interface SSEErrorEvent {
  event: 'error';
  data: { error: string };
}

export type SSEEventTyped = SSEThinkingEvent | SSEToolCallEvent | SSEToolResultEvent | SSEAnswerEvent | SSEErrorEvent;

export function isSSEThinkingEvent(event: { event: string; data: unknown }): event is SSEThinkingEvent {
  return event.event === 'thinking';
}

export function isSSEToolCallEvent(event: { event: string; data: unknown }): event is SSEToolCallEvent {
  return event.event === 'tool_call';
}

export function isSSEToolResultEvent(event: { event: string; data: unknown }): event is SSEToolResultEvent {
  return event.event === 'tool_result';
}

export function isSSEAnswerEvent(event: { event: string; data: unknown }): event is SSEAnswerEvent {
  return event.event === 'answer';
}

export function isSSEErrorEvent(event: { event: string; data: unknown }): event is SSEErrorEvent {
  return event.event === 'error';
}

export interface AppState {
  messages: ChatMessage[];
  streamingId: string | null;
  isLoading: boolean;
  isThinking: boolean;
  models: ModelInfo[];
  currentModel: string;
  skills: SkillInfo[];
  activeSkills: string[];
  mcpServers: string[];
  mcpConnected: number;
  mcpTotal: number;
  theme: 'light' | 'dark';
  sidebarVisible: boolean;
  statusTokens: number;
  sessions: SessionData[];
  currentSessionId: string | null;
  ragDocuments: RagDocument[];
  ragEnabled: boolean;
  selectedKnowledgeSources: string[];
  detailPanelOpen: boolean;
}

export type AppAction =
  | { type: 'ADD_USER_MESSAGE'; payload: ChatMessage }
  | { type: 'START_STREAMING'; payload: { id: string } }
  | { type: 'SET_THINKING'; payload: boolean }
  | { type: 'APPEND_TOKEN'; payload: string }
  | { type: 'SET_TOOL_CALL'; payload: ToolCallBlock }
  | { type: 'UPDATE_TOOL_RESULT'; payload: { result: string; status: string } }
  | { type: 'FINISH_STREAMING' }
  | { type: 'SET_MODELS'; payload: { models: ModelInfo[]; current: string } }
  | { type: 'SET_CURRENT_MODEL'; payload: string }
  | { type: 'SET_SKILLS'; payload: SkillInfo[] }
  | { type: 'SET_ACTIVE_SKILLS'; payload: string[] }
  | { type: 'TOGGLE_ACTIVE_SKILL'; payload: string }
  | { type: 'SET_MCP'; payload: { servers: string[]; connected: number; total: number } }
  | { type: 'SET_THEME'; payload: 'light' | 'dark' }
  | { type: 'TOGGLE_SIDEBAR' }
  | { type: 'CLEAR_MESSAGES' }
  | { type: 'SET_MESSAGES'; payload: ChatMessage[] }
  | { type: 'SET_SESSIONS'; payload: SessionData[] }
  | { type: 'SET_CURRENT_SESSION'; payload: string | null }
  | { type: 'SET_RAG_DOCUMENTS'; payload: { documents: RagDocument[]; enabled: boolean } }
  | { type: 'TOGGLE_KNOWLEDGE_SOURCE'; payload: string }
  | { type: 'TOGGLE_DETAIL_PANEL' }
  | { type: 'SET_STATUS'; payload: Partial<AppState> };
