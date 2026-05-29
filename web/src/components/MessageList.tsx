import React, { useRef, useEffect, memo, useState } from 'react';
import { useApp } from '../context/AppContext';
import { useSSE } from '../hooks/useSSE';
import { processMarkdown } from '../lib/markdown';
import { cn } from '../lib/utils';
import { ChevronDown, ChevronRight, Check, X, Loader2, Copy, CheckCheck } from 'lucide-react';
import type { ChatMessage, ToolCallBlock, TextBlock } from '../types';
import WelcomeScreen from './WelcomeScreen';

function ToolCard({ toolCall }: { toolCall: ToolCallBlock }) {
  const [collapsed, setCollapsed] = useState(toolCall.collapsed !== false);

  const statusIcon = {
    running: <Loader2 size={14} className="animate-spin text-[var(--accent)]" />,
    success: <Check size={14} className="text-[var(--success)]" />,
    error: <X size={14} className="text-[var(--error)]" />,
  }[toolCall.status];

  return (
    <div className="border border-[var(--border-light)] rounded-[8px] overflow-hidden bg-[var(--bg)]">
      <button
        className={cn(
          'flex items-center gap-2 w-full px-3 py-2 text-[13px] text-[var(--text-secondary)] transition-colors',
          'hover:bg-[var(--surface-alt)]',
        )}
        onClick={() => setCollapsed(!collapsed)}
        aria-expanded={!collapsed}
      >
        {statusIcon}
        <span className="font-mono text-[12px]">{toolCall.tool}</span>
        <span className="text-[11px] text-[var(--text-tertiary)]">
          {toolCall.status === 'running' ? 'Running...' : toolCall.status === 'success' ? 'Done' : 'Failed'}
        </span>
        <span className="ml-auto">{collapsed ? <ChevronRight size={12} /> : <ChevronDown size={12} />}</span>
      </button>
      {!collapsed && (
        <div className="px-3 pb-3 pt-2 border-t border-[var(--border-light)]">
          <div className="font-mono text-[12px] text-[var(--text-secondary)] mb-2">
            <strong className="text-[var(--text)]">Params:</strong>{' '}
            {JSON.stringify(toolCall.params, null, 2)}
          </div>
          {toolCall.result && (
            <div>
              <strong className="text-[12px] text-[var(--text)]">Result:</strong>
              <pre className="mt-1 p-2 bg-[var(--bg)] border border-[var(--border-light)] rounded-[6px] font-mono text-[12px] text-[var(--text-secondary)] overflow-x-auto whitespace-pre-wrap">
                {toolCall.result}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      className="opacity-0 group-hover:opacity-100 absolute top-2 right-2 btn-icon"
      onClick={() => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
      aria-label="Copy"
    >
      {copied ? <CheckCheck size={14} className="text-[var(--success)]" /> : <Copy size={14} />}
    </button>
  );
}

function TextBlockRenderer({ content }: { content: string }) {
  const html = processMarkdown(content);
  return <div className="markdown-body text-[14px] leading-relaxed" dangerouslySetInnerHTML={{ __html: html }} />;
}

const MessageItem = memo(function MessageItem({ msg, isStreaming }: { msg: ChatMessage; isStreaming: boolean }) {
  if (msg.blocks) {
    return (
      <div className="card-message animate-message-in">
        <div className="text-[11px] font-semibold uppercase tracking-[0.05em] text-[var(--text-tertiary)] mb-1.5">
          Assistant
        </div>
        <div className="space-y-1.5">
          {msg.blocks.map((block, i) => {
            if (block.type === 'text') return <TextBlockRenderer key={i} content={block.content} />;
            if (block.type === 'tool') return <ToolCard key={block.id} toolCall={block} />;
            return null;
          })}
        </div>
        {isStreaming && (
          <span className="inline-block w-[2px] h-[1em] bg-[var(--accent)] ml-0.5 align-text-bottom animate-blink" />
        )}
      </div>
    );
  }

  return (
    <div className={cn('card-message animate-message-in', msg.role === 'user' ? 'border-l-[3px] border-l-[var(--accent)]' : '')}>
      <div className="text-[11px] font-semibold uppercase tracking-[0.05em] text-[var(--text-tertiary)] mb-1.5">
        {msg.role === 'user' ? 'You' : 'Assistant'}
      </div>
      <div className="text-[14px] leading-relaxed">
        {msg.content && <TextBlockRenderer content={msg.content} />}
        {!msg.content && isStreaming && (
          <span className="inline-block w-[2px] h-[1em] bg-[var(--accent)] animate-blink" />
        )}
      </div>
      {(msg.toolCalls?.length ?? 0) > 0 && (
        <div className="mt-2 space-y-1.5">
          {msg.toolCalls?.map((tc) => <ToolCard key={tc.id} toolCall={tc} />)}
        </div>
      )}
    </div>
  );
});

export default function MessageList() {
  const { state } = useApp();
  const { sendMessage } = useSSE();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [state.messages]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-3" ref={scrollRef}>
      {state.messages.length === 0 ? (
        <WelcomeScreen />
      ) : (
        <div role="log" aria-live="polite" aria-label="Chat messages" className="space-y-3">
          {state.messages.map((msg) => (
            <MessageItem key={msg.id} msg={msg} isStreaming={msg.id === state.streamingId} />
          ))}
        </div>
      )}
    </div>
  );
}
