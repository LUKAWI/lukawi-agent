import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ModelSelector } from '../ModelSelector';

// Mock GSAP (Section dependency)
vi.mock('../../lib/gsap', () => ({
  useGSAP: vi.fn(),
  gsap: { to: vi.fn(), fromTo: vi.fn() },
  getDuration: vi.fn((d: number) => d),
}));

describe('ModelSelector', () => {
  const models = [
    { name: 'deepseek-chat', model: 'deepseek-chat', provider: 'deepseek' },
    { name: 'gpt-4', model: 'gpt-4', provider: 'openai' },
  ];

  it('renders model names', () => {
    render(<ModelSelector models={models} currentModel="deepseek-chat" onSelectModel={vi.fn()} />);
    expect(screen.getByText('deepseek-chat')).toBeDefined();
    expect(screen.getByText('gpt-4')).toBeDefined();
  });

  it('renders provider badges', () => {
    render(<ModelSelector models={models} currentModel="deepseek-chat" onSelectModel={vi.fn()} />);
    expect(screen.getByText('deepseek')).toBeDefined();
    expect(screen.getByText('openai')).toBeDefined();
  });

  it('calls onSelectModel when model clicked', () => {
    const onSelect = vi.fn();
    render(<ModelSelector models={models} currentModel="deepseek-chat" onSelectModel={onSelect} />);
    fireEvent.click(screen.getByText('gpt-4'));
    expect(onSelect).toHaveBeenCalledWith('gpt-4');
  });

  it('renders empty state when no models', () => {
    render(<ModelSelector models={[]} currentModel="" onSelectModel={vi.fn()} />);
    expect(screen.getByText('No models')).toBeDefined();
  });
});
