import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { McpStatus } from '../McpStatus';

// Mock GSAP (Section dependency)
vi.mock('../../lib/gsap', () => ({
  useGSAP: vi.fn(),
  gsap: { to: vi.fn(), fromTo: vi.fn() },
  getDuration: vi.fn((d: number) => d),
}));

describe('McpStatus', () => {
  it('renders server names', () => {
    render(
      <McpStatus
        servers={['sequential-thinking', 'context7']}
        connected={1}
        total={2}
        onConnect={vi.fn()}
        onDisconnect={vi.fn()}
      />
    );
    expect(screen.getByText('sequential-thinking')).toBeDefined();
    expect(screen.getByText('context7')).toBeDefined();
  });

  it('renders Connect and Disconnect buttons when total > 0', () => {
    render(
      <McpStatus servers={['s1']} connected={1} total={1} onConnect={vi.fn()} onDisconnect={vi.fn()} />
    );
    expect(screen.getByText('Connect')).toBeDefined();
    expect(screen.getByText('Disconnect')).toBeDefined();
  });

  it('calls onConnect when Connect clicked', () => {
    const onConnect = vi.fn();
    render(
      <McpStatus servers={['s1']} connected={0} total={1} onConnect={onConnect} onDisconnect={vi.fn()} />
    );
    fireEvent.click(screen.getByText('Connect'));
    expect(onConnect).toHaveBeenCalled();
  });

  it('calls onDisconnect when Disconnect clicked', () => {
    const onDisconnect = vi.fn();
    render(
      <McpStatus servers={['s1']} connected={1} total={1} onConnect={vi.fn()} onDisconnect={onDisconnect} />
    );
    fireEvent.click(screen.getByText('Disconnect'));
    expect(onDisconnect).toHaveBeenCalled();
  });

  it('renders empty state when no servers', () => {
    render(
      <McpStatus servers={[]} connected={0} total={0} onConnect={vi.fn()} onDisconnect={vi.fn()} />
    );
    expect(screen.getByText('No servers')).toBeDefined();
  });
});
