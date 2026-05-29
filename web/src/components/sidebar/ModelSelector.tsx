import { cn } from '../../lib/utils';
import type { ModelInfo } from '../../types';
import { Cpu } from 'lucide-react';
import { Section } from './Section';

export interface ModelSelectorProps {
  models: ModelInfo[];
  currentModel: string;
  onSelectModel: (name: string) => void;
}

export function ModelSelector({ models, currentModel, onSelectModel }: ModelSelectorProps) {
  return (
    <Section title="Models" icon={<Cpu size={14} />} defaultOpen badge={models.length}>
      {models.map((m) => (
        <div
          key={m.name}
          className={cn(
            'flex items-center gap-2 px-2.5 py-1.5 rounded-[6px] text-[13px] cursor-pointer border-l-2 border-transparent transition-colors hover:bg-[var(--surface-alt)]',
            m.name === currentModel && 'bg-[var(--accent-light)] border-l-[var(--accent)]',
          )}
          onClick={() => onSelectModel(m.name)}
        >
          <span className="text-[13px] truncate">{m.model || m.name}</span>
          <span className="ml-auto text-[11px] text-[var(--text-tertiary)] bg-[var(--surface-alt)] px-1 py-0.5 rounded-[3px]">
            {m.provider}
          </span>
        </div>
      ))}
      {models.length === 0 && (
        <div className="px-2.5 py-1.5 text-[12px] italic text-[var(--text-tertiary)]">No models</div>
      )}
    </Section>
  );
}
