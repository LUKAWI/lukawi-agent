import React from 'react';

export default function MCPIcon({ size = 20, className = '', ...props }) {
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
      <rect x="4" y="3" width="16" height="6" rx="1" />
      <rect x="4" y="15" width="16" height="6" rx="1" />
      <path d="M8 6h8" />
      <path d="M8 18h8" />
      <path d="M12 9v6" />
      <path d="M5 12h14" />
    </svg>
  );
}
