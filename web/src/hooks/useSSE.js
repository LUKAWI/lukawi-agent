import { useCallback, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api';

export function useSSE() {
  const { state, dispatch } = useApp();
  const abortRef = useRef(null);

  const sendMessage = useCallback((message) => {
    if (abortRef.current) abortRef.current.abort();

    dispatch({
      type: 'ADD_USER_MESSAGE',
      payload: { id: crypto.randomUUID(), role: 'user', content: message, toolCalls: [], timestamp: Date.now() },
    });

    const assistantId = crypto.randomUUID();
    dispatch({ type: 'START_STREAMING', payload: { id: assistantId } });

    abortRef.current = api.chatStream(message, {
      onEvent(eventType, data) {
        switch (eventType) {
          case 'thinking':
            dispatch({ type: 'APPEND_TOKEN', payload: '\n🧐 Thinking...' });
            break;
          case 'tool_call':
            dispatch({ type: 'APPEND_TOKEN', payload: `\n🔧 Using tool: **${data.tool}**` });
            dispatch({ type: 'SET_TOOL_CALL', payload: data });
            break;
          case 'tool_result':
            dispatch({ type: 'UPDATE_TOOL_RESULT', payload: data });
            break;
          case 'answer':
            dispatch({ type: 'APPEND_TOKEN', payload: data.content || '' });
            break;
          case 'error':
            dispatch({ type: 'APPEND_TOKEN', payload: `\n❌ Error: ${data.error}` });
            break;
          default:
            break;
        }
      },
      onError(err) {
        dispatch({
          type: 'APPEND_TOKEN',
          payload: `\n❌ Connection error: ${err.message}`,
        });
        dispatch({ type: 'FINISH_STREAMING' });
      },
      onDone() {
        dispatch({ type: 'FINISH_STREAMING' });
      },
    });
  }, [dispatch]);

  const clearMessages = useCallback(() => {
    if (abortRef.current) abortRef.current.abort();
    dispatch({ type: 'CLEAR_MESSAGES' });
  }, [dispatch]);

  return { sendMessage, clearMessages, isLoading: state.isLoading };
}