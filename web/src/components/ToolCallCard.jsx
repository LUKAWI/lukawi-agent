import React, { useState } from 'react';
import {
  SpinnerIcon,
  CheckIcon,
  ErrorIcon,
  ChevronDownIcon,
  ChevronRightIcon,
} from './icons';
import './ToolCallCard.css';

const STATUS_LABELS = {
  running: 'Running...',
  success: 'Done',
  error: 'Failed',
};

const STATUS_ICONS = {
  running: SpinnerIcon,
  success: CheckIcon,
  error: ErrorIcon,
};

export default function ToolCallCard({ toolCall }) {
  const [collapsed, setCollapsed] = useState(false);
  const Icon = STATUS_ICONS[toolCall.status] || null;
  const label = STATUS_LABELS[toolCall.status] || toolCall.status;

  const headerLabel = `${toolCall.tool} - ${label}`;

  return (
    <div className={`tool-card tool-${toolCall.status}`}>
      <div
        className="tool-header"
        onClick={() => setCollapsed(!collapsed)}
        role="button"
        tabIndex={0}
        aria-label={headerLabel}
        aria-expanded={!collapsed}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setCollapsed(!collapsed);
          }
        }}
      >
        {Icon && <Icon size={14} className="tool-status-icon" />}
        <span className="tool-name">{toolCall.tool}</span>
        <span className="tool-status">{label}</span>
        {collapsed ? (
          <ChevronRightIcon size={12} className="tool-toggle" />
        ) : (
          <ChevronDownIcon size={12} className="tool-toggle" />
        )}
      </div>
      {!collapsed && (
        <div className="tool-details">
          <div className="tool-params">
            <strong>Params:</strong> {JSON.stringify(toolCall.params, null, 2)}
          </div>
          {toolCall.result && (
            <div className="tool-result">
              <strong>Result:</strong>
              <pre>{toolCall.result}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
