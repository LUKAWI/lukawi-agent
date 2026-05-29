import { useCallback, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api';
import type { ChatMessage } from '../types';

export function useSSE() {
  const { state, dispatch } = useApp();
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    (message: string) => {
      if (abortRef.current) abortRef.current.abort();

      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content: message,
        toolCalls: [],
        timestamp: Date.now(),
      };
      dispatch({ type: 'ADD_USER_MESSAGE', payload: userMsg });

      const assistantId = crypto.randomUUID();
      dispatch({ type: 'START_STREAMING', payload: { id: assistantId } });

      let sessionCaptured = false;

      abortRef.current = api.chatStream(message, {
        sessionId: state.currentSessionId,
        knowledgeSources: state.selectedKnowledgeSources,
        onEvent(eventType, data) {
          switch (eventType) {
            case 'thinking':
              dispatch({ type: 'APPEND_TOKEN', payload: '\n🧐 Thinking...' });
              if (!sessionCaptured && (data as { session_id?: string }).session_id) {
                dispatch({
                  type: 'SET_CURRENT_SESSION',
                  payload: (data as { session_id: string }).session_id,
                });
                sessionCaptured = true;
              }
              break;
            case 'tool_call':
              dispatch({
                type: 'APPEND_TOKEN',
                payload: `\n🔧 Using tool: **${(data as { tool: string }).tool}**`,
              });
              dispatch({
                type: 'SET_TOOL_CALL',
                payload: {
                  type: 'tool',
                  id: crypto.randomUUID(),
                  tool: (data as { tool: string }).tool,
                  params: (data as { params: Record<string, unknown> }).params || {},
                  status: 'running',
                  collapsed: true,
                },
              });
              break;
            case 'tool_result':
              dispatch({
                type: 'UPDATE_TOOL_RESULT',
                payload: {
                  result:
                    typeof (data as { result: unknown }).result === 'string'
                      ? (data as { result: string }).result
                      : JSON.stringify((data as { result: unknown }).result, null, 2),
                  status: (data as { status: string }).status === 'success' ? 'success' : 'error',
                },
              });
              break;
            case 'answer':
              dispatch({ type: 'APPEND_TOKEN', payload: (data as { content: string }).content || '' });
              break;
            case 'error':
              dispatch({ type: 'APPEND_TOKEN', payload: `\n❌ Error: ${(data as { error: string }).error}` });
              break;
          }
        },
        onError(err) {
          dispatch({ type: 'APPEND_TOKEN', payload: `\n❌ Connection error: ${err.message}` });
          dispatch({ type: 'FINISH_STREAMING' });
        },
        onDone() {
          dispatch({ type: 'FINISH_STREAMING' });
        },
      });
    },
    [dispatch, state.currentSessionId],
  );

  const clearMessages = useCallback(() => {
    if (abortRef.current) abortRef.current.abort();
    dispatch({ type: 'CLEAR_MESSAGES' });
  }, [dispatch]);

  return { sendMessage, clearMessages, isLoading: state.isLoading };
}
