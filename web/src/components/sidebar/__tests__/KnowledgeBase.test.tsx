import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { KnowledgeBase } from '../KnowledgeBase';
import React from 'react';

describe('KnowledgeBase', () => {
  const defaultProps = {
    documents: [
      { path: '/docs/readme.md', filename: 'readme.md', chunks: 5 },
      { path: '/docs/guide.txt', filename: 'guide.txt', chunks: 3 },
    ],
    enabled: true,
    selectedSources: ['/docs/readme.md'],
    uploading: false,
    uploadError: null as string | null,
    fileInputRef: { current: null } as React.RefObject<HTMLInputElement>,
    onUpload: vi.fn(),
    onToggleSource: vi.fn(),
    onDelete: vi.fn(),
  };

  it('renders Knowledge header', () => {
    render(<KnowledgeBase {...defaultProps} />);
    expect(screen.getByText('Knowledge')).toBeDefined();
  });

  it('renders document filenames', () => {
    render(<KnowledgeBase {...defaultProps} />);
    expect(screen.getByText('readme.md')).toBeDefined();
    expect(screen.getByText('guide.txt')).toBeDefined();
  });

  it('renders Upload button when enabled', () => {
    render(<KnowledgeBase {...defaultProps} />);
    expect(screen.getByText('Upload')).toBeDefined();
  });

  it('calls onToggleSource when document clicked', () => {
    const onToggle = vi.fn();
    render(<KnowledgeBase {...defaultProps} onToggleSource={onToggle} />);
    fireEvent.click(screen.getByText('guide.txt'));
    expect(onToggle).toHaveBeenCalledWith('/docs/guide.txt');
  });

  it('calls onDelete when delete button clicked', () => {
    const onDelete = vi.fn();
    render(<KnowledgeBase {...defaultProps} onDelete={onDelete} />);
    // Find the trash button near readme.md
    const trashButtons = screen.getAllByRole('button').filter(
      (btn) => btn.querySelector('svg')
    );
    // Click the first trash button (after Upload)
    const deleteBtn = trashButtons.find((btn) =>
      btn.closest('[class*="cursor-pointer"]')
    );
    if (deleteBtn) fireEvent.click(deleteBtn);
    expect(onDelete).toHaveBeenCalled();
  });

  it('renders disabled state when RAG not enabled', () => {
    render(<KnowledgeBase {...defaultProps} enabled={false} />);
    expect(screen.getByText('RAG disabled — enable in settings')).toBeDefined();
  });

  it('renders upload error when present', () => {
    render(<KnowledgeBase {...defaultProps} uploadError="File too large" />);
    expect(screen.getByText('File too large')).toBeDefined();
  });

  it('renders uploading state', () => {
    render(<KnowledgeBase {...defaultProps} uploading={true} />);
    expect(screen.getByText('Uploading...')).toBeDefined();
  });

  it('renders empty state when no documents', () => {
    render(<KnowledgeBase {...defaultProps} documents={[]} />);
    expect(screen.getByText('No documents')).toBeDefined();
  });
});
