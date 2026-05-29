import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SessionList } from '../SessionList';

// Mock GSAP (Section dependency)
vi.mock('../../lib/gsap', () => ({
  useGSAP: vi.fn(),
  gsap: { to: vi.fn(), fromTo: vi.fn() },
  getDuration: vi.fn((d: number) => d),
}));

const baseProps = {
  sessions: [
    { id: '1', name: 'Session A', created_at: '2024-01-01', updated_at: '2024-01-02' },
    { id: '2', name: 'Session B', created_at: '2024-01-03', updated_at: '2024-01-04' },
  ],
  currentSessionId: '1' as string | null,
  editingSession: null as string | null,
  editName: '',
  onNewSession: vi.fn(),
  onSwitchSession: vi.fn(),
  onRename: vi.fn(),
  onDelete: vi.fn(),
  onSetEditingSession: vi.fn(),
  onSetEditName: vi.fn(),
};

describe('SessionList', () => {
  it('renders session names', () => {
    render(<SessionList {...baseProps} />);
    expect(screen.getByText('Session A')).toBeDefined();
    expect(screen.getByText('Session B')).toBeDefined();
  });

  it('renders New Session button', () => {
    render(<SessionList {...baseProps} />);
    expect(screen.getByText('New Session')).toBeDefined();
  });

  it('calls onNewSession when button clicked', () => {
    render(<SessionList {...baseProps} />);
    fireEvent.click(screen.getByText('New Session'));
    expect(baseProps.onNewSession).toHaveBeenCalled();
  });

  it('calls onSwitchSession when session clicked', () => {
    render(<SessionList {...baseProps} />);
    fireEvent.click(screen.getByText('Session B'));
    expect(baseProps.onSwitchSession).toHaveBeenCalledWith('2');
  });

  it('renders edit input when editing', () => {
    render(<SessionList {...baseProps} editingSession="1" editName="Renamed" />);
    const input = screen.getByDisplayValue('Renamed');
    expect(input).toBeDefined();
  });
});
