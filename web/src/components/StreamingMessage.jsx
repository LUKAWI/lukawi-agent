import React, { memo } from 'react';
import { marked } from 'marked';
import './StreamingMessage.css';

const ROLE_LABELS = {
  user: 'You',
  assistant: 'Assistant',
  system: 'Info',
};

const linkRenderer = new marked.Renderer();
linkRenderer.link = ({ href, title, text }) => {
  const titleAttr = title ? ` title="${title}"` : '';
  return `<a href="${href}" target="_blank" rel="noopener noreferrer"${titleAttr}>${text}</a>`;
};

function StreamingMessage({ message, isStreaming }) {
  const label = ROLE_LABELS[message.role] || message.role;

  let contentHtml = null;
  if (message.content) {
    contentHtml = marked.parse(message.content, { breaks: true, renderer: linkRenderer });
  }

  return (
    <div className="streaming-msg">
      <div className="msg-role">{label}</div>
      <div className="msg-content">
        {contentHtml ? (
          <div
            className="markdown-body"
            dangerouslySetInnerHTML={{ __html: contentHtml }}
          />
        ) : (
          <span className="msg-placeholder">
            {isStreaming ? '\u00A0' : '...'}
          </span>
        )}
        {isStreaming && <span className="cursor">|</span>}
      </div>
    </div>
  );
}

export default memo(StreamingMessage);
