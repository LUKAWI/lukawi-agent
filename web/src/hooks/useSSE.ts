import { useCallback, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api';
import type { ChatMessage } from '../types';
import {
  isSSEThinkingEvent,
  isSSEToolCallEvent,
  isSSEToolResultEvent,
  isSSEAnswerEvent,
  isSSEErrorEvent,
} from '../types';

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
          const event = { event: eventType, data };

          if (isSSEThinkingEvent(event)) {
            dispatch({ type: 'SET_THINKING', payload: true });
            if (!sessionCaptured && event.data.session_id) {
              dispatch({ type: 'SET_CURRENT_SESSION', payload: event.data.session_id });
              sessionCaptured = true;
            }
          } else if (isSSEToolCallEvent(event)) {
            dispatch({
              type: 'SET_TOOL_CALL',
              payload: {
                type: 'tool',
                id: crypto.randomUUID(),
                tool: event.data.tool,
                params: event.data.params || {},
                status: 'running',
                collapsed: true,
              },
            });
          } else if (isSSEToolResultEvent(event)) {
            dispatch({
              type: 'UPDATE_TOOL_RESULT',
              payload: {
                result:
                  typeof event.data.result === 'string'
                    ? event.data.result
                    : JSON.stringify(event.data.result, null, 2),
                status: event.data.status === 'success' ? 'success' : 'error',
              },
            });
          } else if (isSSEAnswerEvent(event)) {
            dispatch({ type: 'APPEND_TOKEN', payload: event.data.content });
          } else if (isSSEErrorEvent(event)) {
            dispatch({ type: 'APPEND_TOKEN', payload: `\n❌ Error: ${event.data.error}` });
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
    [dispatch, state.currentSessionId, state.selectedKnowledgeSources],
  );

  const clearMessages = useCallback(() => {
    if (abortRef.current) abortRef.current.abort();
    dispatch({ type: 'CLEAR_MESSAGES' });
  }, [dispatch]);

  return { sendMessage, clearMessages, isLoading: state.isLoading };
}
