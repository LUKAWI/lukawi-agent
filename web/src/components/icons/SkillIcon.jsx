import React from 'react';

export default function SkillIcon({ size = 20, className = '', ...props }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      {...props}
    >
      <path d="M12 3a2 2 0 0 1 2 2v1h3a2 2 0 0 1 2 2v2h1a2 2 0 0 1 0 4h-1v2a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-2H4a2 2 0 0 1 0-4h1V8a2 2 0 0 1 2-2h3V5a2 2 0 0 1 2-2z" />
    </svg>
  );
}
