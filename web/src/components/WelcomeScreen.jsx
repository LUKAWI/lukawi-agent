import React from 'react';
import './WelcomeScreen.css';

const EXAMPLES = [
  'What can you do?',
  'Help me write code',
  'Search the web for latest news',
];

const APP_VERSION = '0.1.0';

export default function WelcomeScreen({ onExampleClick }) {
  return (
    <div className="welcome-screen">
      <div className="welcome-content">
        <h1 className="welcome-title">Lukawi Agent</h1>
        <p className="welcome-description">
          Your AI assistant with tools. Ask questions, write code, browse the web, and more.
        </p>
        <div className="welcome-examples">
          {EXAMPLES.map((text) => (
            <button
              key={text}
              className="welcome-example-btn"
              onClick={() => onExampleClick?.(text)}
            >
              {text}
            </button>
          ))}
        </div>
      </div>
      <div className="welcome-version">v{APP_VERSION}</div>
    </div>
  );
}
