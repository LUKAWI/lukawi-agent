import React from 'react';
import MessageList from './MessageList';
import InputBar from './InputBar';

export default function ChatPanel() {
  return (
    <div className="flex flex-col flex-1 h-full min-w-0 bg-[var(--bg)]">
      <MessageList />
      <InputBar />
    </div>
  );
}
