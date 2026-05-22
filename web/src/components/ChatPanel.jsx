import React from 'react';
import { useSSE } from '../hooks/useSSE';
import MessageList from './MessageList';
import InputBar from './InputBar';
import './ChatPanel.css';

export default function ChatPanel() {
  const { sendMessage } = useSSE();

  return (
    <div className="chat-panel">
      <MessageList onSendMessage={sendMessage} />
      <InputBar />
    </div>
  );
}