import React from 'react';

export default function SendIcon({ size = 20, className = '', ...props }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 20 20"
      fill="currentColor"
      stroke="none"
      className={className}
      aria-hidden="true"
      {...props}
    >
      <path d="M3.4 2.9a1 1 0 0 0-1 1.7l6.2 3.5a1 1 0 0 1 0 1.8l-6.2 3.5a1 1 0 0 0 1 1.7l16-7.8a1 1 0 0 0 0-1.8Z" />
    </svg>
  );
}
