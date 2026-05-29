import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SkillToggle } from '../SkillToggle';

// Mock GSAP (Section dependency)
vi.mock('../../lib/gsap', () => ({
  useGSAP: vi.fn(),
  gsap: { to: vi.fn(), fromTo: vi.fn() },
  getDuration: vi.fn((d: number) => d),
}));

describe('SkillToggle', () => {
  const skills = [
    { name: 'web-search' },
    { name: 'code-runner' },
  ];

  it('renders skill names', () => {
    render(<SkillToggle skills={skills} activeSkills={['web-search']} onToggleSkill={vi.fn()} />);
    expect(screen.getByText('web-search')).toBeDefined();
    expect(screen.getByText('code-runner')).toBeDefined();
  });

  it('calls onToggleSkill when skill clicked', () => {
    const onToggle = vi.fn();
    render(<SkillToggle skills={skills} activeSkills={['web-search']} onToggleSkill={onToggle} />);
    fireEvent.click(screen.getByText('code-runner'));
    expect(onToggle).toHaveBeenCalledWith('code-runner');
  });

  it('renders empty state when no skills', () => {
    render(<SkillToggle skills={[]} activeSkills={[]} onToggleSkill={vi.fn()} />);
    expect(screen.getByText('No skills')).toBeDefined();
  });
});
