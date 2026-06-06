import { useRef } from 'react';
import { cn } from '../lib/utils';
import { useApp } from '../context/AppContext';
import { useGSAP, gsap, getDuration } from '../lib/gsap';
import { api } from '../api';
import { useKnowledgeUpload } from '../hooks/useKnowledgeUpload';
import { useSessions } from '../hooks/useSessions';
import { SessionList } from './sidebar/SessionList';
import { ModelSelector } from './sidebar/ModelSelector';
import { SkillToggle } from './sidebar/SkillToggle';
import { McpStatus } from './sidebar/McpStatus';
import { KnowledgeBase } from './sidebar/KnowledgeBase';

export default function Sidebar() {
  const { state, dispatch } = useApp();
  const sidebarRef = useRef<HTMLElement>(null);
  const {
    sessions, confirmDelete, editingSession, editName,
    setConfirmDelete, setEditingSession, setEditName,
    handleNewSession, handleSwitchSession, handleRename, handleDelete,
  } = useSessions();
  const { uploading, uploadError, fileInputRef, handleFileUpload } = useKnowledgeUpload();

  useGSAP(() => {
    if (!sidebarRef.current) return;

    if (state.sidebarVisible) {
      gsap.fromTo(sidebarRef.current,
        { width: 0, opacity: 0 },
        { width: 260, opacity: 1, duration: getDuration(0.3), ease: "power2.out" }
      );
    } else {
      gsap.to(sidebarRef.current, {
        width: 0,
        opacity: 0,
        duration: getDuration(0.25),
        ease: "power2.in",
      });
    }
  }, { scope: sidebarRef, dependencies: [state.sidebarVisible] });

  return (
    <aside
      ref={sidebarRef}
      className={cn(
        'shrink-0 h-full flex flex-col bg-[var(--surface)] border-r border-[var(--border)] overflow-hidden',
        !state.sidebarVisible && 'border-r-0',
      )}
      style={{
        width: state.sidebarVisible ? 260 : 0,
        opacity: state.sidebarVisible ? 1 : 0,
      }}
    >
      {/* Top: Sessions - always visible */}
      <div className="shrink-0 p-2 pb-0">
        <SessionList
          sessions={sessions}
          currentSessionId={state.currentSessionId}
          editingSession={editingSession}
          editName={editName}
          onNewSession={handleNewSession}
          onSwitchSession={handleSwitchSession}
          onRename={handleRename}
          onDelete={(id: string) => setConfirmDelete({ type: 'session', id })}
          onSetEditingSession={setEditingSession}
          onSetEditName={setEditName}
        />
      </div>

      <div className="border-t border-[var(--border)] mx-2 my-2" />

      {/* Middle: Models, Skills, MCP - scrollable */}
      <div className="flex-1 overflow-y-auto p-2">
        <ModelSelector
          models={state.models}
          currentModel={state.currentModel}
          onSelectModel={(name: string) => {
            api.useModel(name);
            dispatch({ type: 'SET_CURRENT_MODEL', payload: name });
          }}
        />
        <SkillToggle
          skills={state.skills}
          activeSkills={state.activeSkills}
          onToggleSkill={(name: string) => {
            const enabled = !state.activeSkills.includes(name);
            api.toggleSkill(name, enabled);
            if (enabled) {
              api.loadSkill(name);
            }
            dispatch({ type: 'TOGGLE_ACTIVE_SKILL', payload: name });
          }}
        />
        <McpStatus
          servers={state.mcpServers}
          connected={state.mcpConnected}
          total={state.mcpTotal}
          onConnect={() => api.connectMcp().then(() => api.getMcp().then((d) => dispatch({ type: 'SET_MCP', payload: d })))}
          onDisconnect={() => api.disconnectMcp().then(() => api.getMcp().then((d) => dispatch({ type: 'SET_MCP', payload: d })))}
        />
      </div>

      <div className="border-t border-[var(--border)] mx-2 my-2" />

      {/* Bottom: Knowledge - always visible */}
      <KnowledgeBase
        documents={state.ragDocuments}
        enabled={state.ragEnabled}
        selectedSources={state.selectedKnowledgeSources}
        uploading={uploading}
        uploadError={uploadError}
        fileInputRef={fileInputRef}
        onUpload={handleFileUpload}
        onToggleSource={(path: string) => dispatch({ type: 'TOGGLE_KNOWLEDGE_SOURCE', payload: path })}
        onDelete={(path: string) => setConfirmDelete({ type: 'knowledge', path })}
      />

      {/* Confirm delete bar */}
      {confirmDelete && (
        <div className="flex items-center gap-2 px-3 py-2 border-t border-[var(--border)] bg-[var(--surface)] animate-[fade-in_200ms_ease]">
          <span className="flex-1 text-[12px] font-semibold text-[var(--text)]">
            Delete {confirmDelete.type}?
          </span>
          <button className="px-2 py-1 text-[11px] font-semibold rounded-[6px] border border-[var(--border)] bg-[var(--surface-alt)] text-[var(--text)] hover:bg-[var(--error)] hover:text-white hover:border-[var(--error)] transition-colors" onClick={handleDelete}>
            Delete
          </button>
          <button className="px-2 py-1 text-[11px] font-semibold rounded-[6px] border border-[var(--border)] bg-[var(--surface-alt)] text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors" onClick={() => setConfirmDelete(null)}>
            Cancel
          </button>
        </div>
      )}
    </aside>
  );
}
