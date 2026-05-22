import React, { useRef, useEffect, memo } from 'react';
import { useApp } from '../context/AppContext';
import StreamingMessage from './StreamingMessage';
import ToolCallCard from './ToolCallCard';
import WelcomeScreen from './WelcomeScreen';
import './MessageList.css';

const MessageItem = memo(function MessageItem({ msg, isStreaming }) {
  return (
    <div className={`message message-${msg.role}`}>
      <StreamingMessage message={msg} isStreaming={isStreaming} />
      {msg.toolCalls && msg.toolCalls.length > 0 && (
        <div className="tool-calls">
          {msg.toolCalls.map((tc) => (
            <ToolCallCard key={tc.id} toolCall={tc} />
          ))}
        </div>
      )}
    </div>
  );
});

function MessageList({ onSendMessage }) {
  const { state } = useApp();
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [state.messages]);

  return (
    <div className="message-list" ref={scrollRef}>
      {state.messages.length === 0 ? (
        <WelcomeScreen onExampleClick={onSendMessage} />
      ) : (
        <div role="log" aria-live="polite" aria-label="Chat messages">
          {state.messages.map((msg) => (
            <MessageItem
              key={msg.id}
              msg={msg}
              isStreaming={msg.id === state.streamingId}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default memo(MessageList);
