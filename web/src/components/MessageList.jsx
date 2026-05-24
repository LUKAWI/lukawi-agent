import React, { useRef, useEffect, memo } from 'react';
import { useApp } from '../context/AppContext';
import { marked } from 'marked';
import StreamingMessage from './StreamingMessage';
import ToolCallCard from './ToolCallCard';
import WelcomeScreen from './WelcomeScreen';
import './MessageList.css';

const linkRenderer = new marked.Renderer();
linkRenderer.link = ({ href, title, text }) => {
  const titleAttr = title ? ` title="${title}"` : '';
  return `<a href="${href}" target="_blank" rel="noopener noreferrer"${titleAttr}>${text}</a>`;
};

const AssistantMessage = memo(function AssistantMessage({ msg, isStreaming }) {
  if (msg.blocks) {
    return (
      <div className={`message message-${msg.role}`}>
        <div className="msg-role">Assistant</div>
        <div className="msg-blocks">
          {msg.blocks.map((block, i) => {
            if (block.type === 'text') {
              return <TextBlock key={i} content={block.content} />;
            }
            if (block.type === 'tool') {
              return <ToolCallCard key={block.id} toolCall={block} />;
            }
            return null;
          })}
        </div>
        {isStreaming && <span className="cursor">|</span>}
      </div>
    );
  }
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

const TextBlock = memo(function TextBlock({ content }) {
  const html = marked.parse(content, { breaks: true, renderer: linkRenderer });
  return <div className="markdown-body" dangerouslySetInnerHTML={{ __html: html }} />;
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
            <AssistantMessage
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
