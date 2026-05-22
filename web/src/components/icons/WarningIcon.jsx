import React from 'react';

export default function WarningIcon({ size = 20, className = '', ...props }) {
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
      <path d="M12 3a1 1 0 0 0-.87.5L2.17 19.5A1 1 0 0 0 3.04 21h17.92a1 1 0 0 0 .87-1.5L12.87 3.5A1 1 0 0 0 12 3z" />
      <path d="M12 10v4M12 17h.01" />
    </svg>
  );
}
