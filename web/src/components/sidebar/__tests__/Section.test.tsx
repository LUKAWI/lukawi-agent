import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Section } from '../Section';

// Mock GSAP
vi.mock('../../lib/gsap', () => ({
  useGSAP: vi.fn(),
  gsap: { to: vi.fn(), fromTo: vi.fn() },
  getDuration: vi.fn((d: number) => d),
}));

describe('Section', () => {
  it('renders title and icon', () => {
    render(
      <Section title="Test Section" icon={<span data-testid="icon">icon</span>}>
        <div>Child content</div>
      </Section>
    );
    expect(screen.getByText('Test Section')).toBeDefined();
    expect(screen.getByTestId('icon')).toBeDefined();
  });

  it('renders badge when provided', () => {
    render(
      <Section title="Models" icon={<span />} badge={5}>
        <div>Content</div>
      </Section>
    );
    expect(screen.getByText('5')).toBeDefined();
  });

  it('renders badge as string', () => {
    render(
      <Section title="MCP" icon={<span />} badge="3/5">
        <div>Content</div>
      </Section>
    );
    expect(screen.getByText('3/5')).toBeDefined();
  });
});
