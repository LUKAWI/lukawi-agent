import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useKnowledgeUpload } from './useKnowledgeUpload';

// Mock the API module
vi.mock('../api', () => ({
  api: {
    uploadRagDocument: vi.fn().mockResolvedValue(undefined),
    getRagDocuments: vi.fn().mockResolvedValue({ documents: [], enabled: false }),
  },
}));

// Mock the context
vi.mock('../context/AppContext', () => ({
  useApp: () => ({
    state: {},
    dispatch: vi.fn(),
  }),
}));

describe('useKnowledgeUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default values', () => {
    const { result } = renderHook(() => useKnowledgeUpload());
    expect(result.current.uploading).toBe(false);
    expect(result.current.uploadError).toBeNull();
    expect(result.current.fileInputRef.current).toBeNull();
  });

  it('should handle file upload', async () => {
    const { result } = renderHook(() => useKnowledgeUpload());

    const mockEvent = {
      target: {
        files: [new File(['content'], 'test.txt', { type: 'text/plain' })],
        value: '',
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    await act(async () => {
      await result.current.handleFileUpload(mockEvent);
    });

    expect(result.current.uploading).toBe(false);
    expect(result.current.uploadError).toBeNull();
  });

  it('should handle upload error', async () => {
    const { api } = await import('../api');
    vi.mocked(api.uploadRagDocument).mockRejectedValueOnce(new Error('Upload failed'));

    const { result } = renderHook(() => useKnowledgeUpload());

    const mockEvent = {
      target: {
        files: [new File(['content'], 'test.txt', { type: 'text/plain' })],
        value: '',
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    await act(async () => {
      await result.current.handleFileUpload(mockEvent);
    });

    expect(result.current.uploading).toBe(false);
    expect(result.current.uploadError).toBe('Upload failed');
  });
});
