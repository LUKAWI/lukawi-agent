import React, { useRef, useEffect, memo, useState } from 'react';
import { useApp } from '../context/AppContext';
import { useSSE } from '../hooks/useSSE';
import { processMarkdown } from '../lib/markdown';
import { cn } from '../lib/utils';
import { gsap, useGSAP, getDuration } from '../lib/gsap';
import { ChevronDown, ChevronRight, Check, X, Loader2, Copy, CheckCheck } from 'lucide-react';
import type { ChatMessage, ToolCallBlock, TextBlock } from '../types';
import WelcomeScreen from './WelcomeScreen';
import ThinkingIndicator from './ThinkingIndicator';

function ToolCard({ toolCall }: { toolCall: ToolCallBlock }) {
  const [collapsed, setCollapsed] = useState(toolCall.collapsed !== false);
  const contentRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    if (!contentRef.current) return;

    if (collapsed) {
      gsap.to(contentRef.current, {
        height: 0,
        opacity: 0,
        duration: getDuration(0.3),
        ease: "power2.inOut",
        onComplete: () => {
          if (contentRef.current) {
            contentRef.current.style.display = "none";
          }
        }
      });
    } else {
      contentRef.current.style.display = "block";
      gsap.fromTo(contentRef.current,
        { height: 0, opacity: 0 },
        { height: "auto", opacity: 1, duration: getDuration(0.3), ease: "power2.inOut" }
      );
    }
  }, { dependencies: [collapsed] });

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
      <div
        ref={contentRef}
        className="px-3 pb-3 pt-2 border-t border-[var(--border-light)]"
        style={collapsed ? { display: 'none', height: 0, opacity: 0 } : undefined}
      >
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
  const { state } = useApp();
  
  if (msg.blocks) {
    return (
      <div className="card-message">
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
        {isStreaming && !state.isThinking && (
          <span className="inline-block w-[2px] h-[1em] bg-[var(--accent)] ml-0.5 align-text-bottom animate-blink" />
        )}
        {isStreaming && state.isThinking && (
          <ThinkingIndicator isVisible={state.isThinking} />
        )}
      </div>
    );
  }

  return (
    <div className={cn('card-message', msg.role === 'user' ? 'border-l-[3px] border-l-[var(--accent)]' : '')}>
      <div className="text-[11px] font-semibold uppercase tracking-[0.05em] text-[var(--text-tertiary)] mb-1.5">
        {msg.role === 'user' ? 'You' : 'Assistant'}
      </div>
      <div className="text-[14px] leading-relaxed">
        {msg.content && <TextBlockRenderer content={msg.content} />}
        {!msg.content && isStreaming && state.isThinking && (
          <ThinkingIndicator isVisible={state.isThinking} />
        )}
        {!msg.content && isStreaming && !state.isThinking && (
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
  const listRef = useRef<HTMLDivElement>(null);
  const prevLengthRef = useRef(0);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [state.messages]);

  useGSAP(() => {
    const messages = state.messages;
    const prevLength = prevLengthRef.current;
    const newCount = messages.length - prevLength;

    if (newCount > 0 && listRef.current) {
      const allCards = listRef.current.querySelectorAll('.card-message');
      const newCards = Array.from(allCards).slice(prevLength);

      if (newCards.length > 0) {
        gsap.from(newCards, {
          y: 20,
          opacity: 0,
          scale: 0.98,
          stagger: 0.08,
          duration: getDuration(0.4),
          ease: 'power2.out',
          clearProps: 'all',
        });
      }
    }

    prevLengthRef.current = messages.length;
  }, { dependencies: [state.messages.length], scope: listRef });

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-3" ref={scrollRef}>
      {state.messages.length === 0 ? (
        <WelcomeScreen />
      ) : (
        <div ref={listRef} role="log" aria-live="polite" aria-label="Chat messages" className="space-y-3">
          {state.messages.map((msg) => (
            <MessageItem key={msg.id} msg={msg} isStreaming={msg.id === state.streamingId} />
          ))}
        </div>
      )}
    </div>
  );
}
