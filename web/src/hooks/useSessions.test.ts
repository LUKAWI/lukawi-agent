import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useSessions } from './useSessions';

// Mock the API module
vi.mock('../api', () => ({
  api: {
    getSessions: vi.fn().mockResolvedValue({ sessions: [] }),
    getModels: vi.fn().mockResolvedValue({ models: [], current: '' }),
    getSkills: vi.fn().mockResolvedValue({ skills: [] }),
    getMcp: vi.fn().mockResolvedValue({ servers: [], connected: 0, total: 0 }),
    getRagDocuments: vi.fn().mockResolvedValue({ documents: [], enabled: false }),
    createSession: vi.fn().mockResolvedValue({ id: '1', name: '新对话', created_at: '', updated_at: '' }),
    getSessionMessages: vi.fn().mockResolvedValue({ messages: [] }),
    renameSession: vi.fn().mockResolvedValue(undefined),
    deleteSession: vi.fn().mockResolvedValue(undefined),
    deleteRagDocument: vi.fn().mockResolvedValue(undefined),
  },
}));

// Mock the context with stable dispatch reference
const mockDispatch = vi.fn();
vi.mock('../context/AppContext', () => ({
  useApp: () => ({
    state: { currentSessionId: null },
    dispatch: mockDispatch,
  }),
}));

describe('useSessions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with empty sessions', () => {
    const { result } = renderHook(() => useSessions());
    expect(result.current.sessions).toEqual([]);
    expect(result.current.confirmDelete).toBeNull();
    expect(result.current.editingSession).toBeNull();
    expect(result.current.editName).toBe('');
  });

  it('should handle new session creation', async () => {
    const { result } = renderHook(() => useSessions());

    await act(async () => {
      await result.current.handleNewSession();
    });

    expect(result.current.sessions).toHaveLength(1);
    expect(result.current.sessions[0].name).toBe('新对话');
  });

  it('should handle session rename', async () => {
    const { result } = renderHook(() => useSessions());

    // Set up editing state
    act(() => {
      result.current.setEditingSession('1');
      result.current.setEditName('New Name');
    });

    await act(async () => {
      await result.current.handleRename('1');
    });

    expect(result.current.editingSession).toBeNull();
  });
});
