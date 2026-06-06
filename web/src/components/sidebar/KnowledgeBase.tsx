import { cn } from '../../lib/utils';
import type { RagDocument } from '../../types';
import { Upload, Check, FileText, Trash2, BookOpen } from 'lucide-react';

export interface KnowledgeBaseProps {
  documents: RagDocument[];
  enabled: boolean;
  selectedSources: string[];
  uploading: boolean;
  uploadError: string | null;
  fileInputRef: React.RefObject<HTMLInputElement>;
  onUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onToggleSource: (path: string) => void;
  onDelete: (path: string) => void;
}

export function KnowledgeBase({
  documents,
  enabled,
  selectedSources,
  uploading,
  uploadError,
  fileInputRef,
  onUpload,
  onToggleSource,
  onDelete,
}: KnowledgeBaseProps) {
  return (
    <div className="shrink-0 p-2 pt-0">
      <div className="flex items-center gap-2 px-2.5 py-1.5 mb-1 text-[11px] font-semibold text-[var(--accent)] bg-[var(--accent-light)] rounded-[6px]">
        <BookOpen size={14} />
        <span className="flex-1">Knowledge</span>
        <span className="text-[10px] font-normal text-[var(--text-tertiary)]">{selectedSources.length}/{documents.length}</span>
      </div>
      <div className="px-2.5 py-1">
        {enabled ? (
          <>
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.md"
              className="hidden"
              onChange={onUpload}
            />
            <button
              className="flex items-center justify-center gap-1.5 w-full px-2.5 py-1.5 mb-1 text-[12px] font-semibold rounded-[6px] border-2 border-dashed border-[var(--border)] text-[var(--accent)] hover:bg-[var(--accent-light)] hover:border-[var(--accent)] transition-colors disabled:opacity-50"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
            >
              <Upload size={14} />
              {uploading ? 'Uploading...' : 'Upload'}
            </button>
            {uploadError && (
              <div className="px-2 py-1 mb-1 text-[11px] text-[var(--error)] bg-[var(--error-light)] rounded-[6px] border-l-2 border-[var(--error)]">
                {uploadError}
              </div>
            )}
            {documents.map((doc) => (
              <div
                key={doc.path}
                className={cn(
                  'flex items-center gap-2 px-2 py-1 rounded-[6px] text-[12px] cursor-pointer border-l-2 border-transparent transition-colors hover:bg-[var(--surface-alt)]',
                  selectedSources.includes(doc.path) && 'bg-[var(--accent-light)] border-l-[var(--accent)]',
                )}
                onClick={() => onToggleSource(doc.path)}
              >
                {selectedSources.includes(doc.path) ? (
                  <Check size={12} className="text-[var(--accent)] shrink-0" />
                ) : (
                  <FileText size={12} className="text-[var(--text-tertiary)] shrink-0" />
                )}
                <span className="truncate">{doc.filename}</span>
                <span className="text-[10px] text-[var(--text-tertiary)]">{doc.chunks} chunks</span>
                <button
                  className="ml-auto opacity-100 text-[var(--text-tertiary)] hover:text-[var(--error)] transition-all"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(doc.path);
                  }}
                >
                  <Trash2 size={10} />
                </button>
              </div>
            ))}
            {documents.length === 0 && (
              <div className="text-[12px] italic text-[var(--text-tertiary)] px-1">No documents</div>
            )}
          </>
        ) : (
          <div className="flex items-center gap-2 px-2 py-1.5 text-[11px] text-[var(--text-tertiary)] bg-[var(--surface-alt)] rounded-[6px] border-l-2 border-[var(--border)]">
            <span>RAG disabled — enable in settings</span>
          </div>
        )}
      </div>
    </div>
  );
}
