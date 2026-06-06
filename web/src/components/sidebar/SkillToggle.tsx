import { cn } from '../../lib/utils';
import type { SkillInfo } from '../../types';
import { Puzzle } from 'lucide-react';
import { Section } from './Section';

export interface SkillToggleProps {
  skills: SkillInfo[];
  activeSkills: string[];
  onToggleSkill: (name: string) => void;
}

export function SkillToggle({ skills, activeSkills, onToggleSkill }: SkillToggleProps) {
  return (
    <Section title="Skills" icon={<Puzzle size={14} />} defaultOpen={false} badge={activeSkills.length}>
      {skills.map((s) => (
        <div
          key={s.name}
          className={cn(
            'flex items-center gap-2 px-2.5 py-1.5 rounded-[6px] text-[13px] cursor-pointer border-l-2 border-transparent transition-colors',
            activeSkills.includes(s.name)
              ? 'bg-[var(--accent-light)] border-l-[var(--accent)]'
              : 'hover:bg-[var(--surface-alt)]',
          )}
          onClick={() => onToggleSkill(s.name)}
        >
          <span className="truncate">{s.name}</span>
        </div>
      ))}
      {skills.length === 0 && (
        <div className="px-2.5 py-1.5 text-[12px] italic text-[var(--text-tertiary)]">No skills</div>
      )}
    </Section>
  );
}
