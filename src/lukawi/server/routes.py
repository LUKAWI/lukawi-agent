"""REST API routes for Lukawi server."""
from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel


class ModelUseRequest(BaseModel):
    name: str


class SkillLoadRequest(BaseModel):
    name: str


class SkillToggleRequest(BaseModel):
    name: str
    enabled: bool


class ThemeRequest(BaseModel):
    theme: str


class SaveMemoryRequest(BaseModel):
    content: str


class CreateSessionRequest(BaseModel):
    name: str = "新对话"


class DeleteDocumentRequest(BaseModel):
    source_path: str


def create_router(state) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/models")
    async def get_models():
        if not state.model_registry:
            return {"models": [], "current": None}
        models = [
            {
                "name": key,
                "model": info.name,
                "provider": info.provider,
                "display_name": info.display_name if info.display_name else None
            }
            for key, info in state.model_registry.list_registered()
        ]
        return {"models": models, "current": state.model_registry.current_name}

    @router.post("/models/use")
    async def use_model(req: ModelUseRequest):
        if not state.model_registry:
            raise HTTPException(400, "No model registry")
        if not state.model_registry.has(req.name):
            raise HTTPException(400, f"Model '{req.name}' not found")
        state.model_registry.use(req.name)
        if state.agent:
            provider = state.model_registry.current
            state.agent.switch_model(req.name, provider)
        return {"ok": True}

    @router.get("/skills")
    async def get_skills():
        if not state.skill_loader:
            return {"skills": []}
        skills = [
            {
                "name": s.name,
                "description": s.description,
                "triggers": list(s.triggers) if s.triggers else [],
                "selected": s.name in state.selected_skills,
            }
            for s in state.skill_loader.list_skills()
        ]
        return {"skills": skills}

    @router.post("/skills/toggle")
    async def toggle_skill(req: SkillToggleRequest):
        if not state.skill_loader:
            raise HTTPException(400, "Skill system not initialized")
        skill = state.skill_loader.get_skill(req.name)
        if not skill:
            raise HTTPException(400, f"Skill '{req.name}' not found")
        if req.enabled:
            state.selected_skills.add(req.name)
        else:
            state.selected_skills.discard(req.name)
            state.active_skills.pop(req.name, None)
        return {"ok": True, "selected": list(state.selected_skills)}

    @router.post("/skills/load")
    async def load_skill(req: SkillLoadRequest):
        if not state.skill_loader:
            raise HTTPException(400, "Skill system not initialized")
        skill = state.skill_loader.get_skill(req.name)
        if not skill:
            raise HTTPException(400, f"Skill '{req.name}' not found")
        from lukawi.skills.executor import build_skill_injection

        injection = build_skill_injection(skill)
        state.active_skills[skill.name] = injection
        if state.agent:
            state.agent.inject_system_message(injection)
        return {"ok": True}

    @router.get("/mcp")
    async def get_mcp():
        connected = state.mcp_manager.connected_count if state.mcp_manager else 0
        servers = state.mcp_manager.connected_servers if state.mcp_manager else []
        total = len(state.mcp_configs) if state.mcp_configs else 0
        return {"servers": list(servers), "connected": connected, "total": total}

    @router.post("/mcp/connect")
    async def connect_mcp():
        if not state.mcp_manager:
            raise HTTPException(400, "No MCP manager")

        await state.mcp_manager.connect_all(state.mcp_configs)
        if state.tool_registry:
            await state.mcp_manager.register_tools(state.tool_registry)
        return {"ok": True}

    @router.post("/mcp/disconnect")
    async def disconnect_mcp():
        if not state.mcp_manager:
            raise HTTPException(400, "No MCP manager")
        await state.mcp_manager.disconnect_all()
        return {"ok": True}

    @router.get("/config")
    async def get_config():
        tui = state.tui_config
        return {
            "theme": tui.theme if tui else "light",
            "showTimestamps": tui.show_timestamps if tui else True,
            "showToolDetails": tui.show_tool_details if tui else True,
            "maxSteps": (
                state.config.agent.max_steps
                if state.config and hasattr(state.config, "agent")
                else 10
            ),
        }

    @router.post("/config/theme")
    async def set_theme(req: ThemeRequest):
        if state.tui_config:
            state.tui_config.theme = req.theme
        return {"ok": True}

    @router.get("/status")
    async def get_status():
        model_name = state.model_registry.current_name if state.model_registry else ""
        mcp_conn = state.mcp_manager.connected_count if state.mcp_manager else 0
        mcp_total = len(state.mcp_configs) if state.mcp_configs else 0
        return {
            "model": model_name,
            "tokens": 0,
            "mcpConnected": mcp_conn,
            "mcpTotal": mcp_total,
            "activeSkills": len(state.active_skills),
        }

    @router.get("/memory/search")
    async def search_memory(q: str = "", limit: int = 10, session_id: str = ""):
        if not state.memory_manager:
            raise HTTPException(400, "Memory system not initialized")
        if not q.strip():
            return {"memories": []}
        sid = session_id.strip() or None
        memories = await state.memory_manager.recall(query=q, limit=limit, session_id=sid)
        return {
            "memories": [
                {
                    "id": m.id,
                    "content": m.content,
                    "metadata": m.metadata,
                    "created_at": m.created_at.isoformat(),
                    "score": m.score,
                }
                for m in memories
            ]
        }

    @router.post("/memory/save")
    async def save_memory(req: SaveMemoryRequest):
        if not state.memory_manager:
            raise HTTPException(400, "Memory system not initialized")
        memory_id = await state.memory_manager.save_conversation(summary=req.content)
        return {"id": memory_id, "ok": True}

    @router.post("/memory/clear")
    async def clear_memory(session_id: str = ""):
        if not state.memory_manager:
            raise HTTPException(400, "Memory system not initialized")
        cleared = 0
        if state.memory_manager.longterm:
            await state.memory_manager.longterm.clear(user_id="default")
        if state.memory_manager.rag:
            if session_id:
                cleared = await state.memory_manager.rag.store.clear_conversations_by_session(session_id)
            else:
                cleared = await state.memory_manager.rag.store.clear_conversations()
        return {"ok": True, "cleared": cleared, "session_id": session_id or None}

    @router.get("/memory/stats")
    async def memory_stats():
        if not state.memory_manager:
            return {"enabled": False, "mode": "none", "session_messages": 0}
        mode = "rag" if state.memory_manager.rag else ("longterm" if state.memory_manager.longterm else "session_only")
        return {
            "enabled": True,
            "mode": mode,
            "session_messages": state.memory_manager.session.message_count,
            "rag_enabled": state.memory_manager.rag is not None,
        }

    @router.get("/sessions")
    async def list_sessions():
        if not state.memory_manager or not state.memory_manager.session_manager:
            return {"sessions": []}
        sessions = await state.memory_manager.session_manager.list_sessions()
        return {
            "sessions": [
                {
                    "id": s.id,
                    "name": s.name,
                    "message_count": s.message_count,
                    "created_at": s.created_at.isoformat(),
                    "updated_at": s.updated_at.isoformat(),
                }
                for s in sessions
            ]
        }

    @router.post("/sessions")
    async def create_session(req: CreateSessionRequest):
        if not state.memory_manager or not state.memory_manager.session_manager:
            raise HTTPException(400, "Session manager not initialized")
        session = await state.memory_manager.session_manager.create_session(name=req.name)
        return {"id": session.id, "name": session.name}

    @router.patch("/sessions/{session_id}")
    async def rename_session(session_id: str, req: CreateSessionRequest):
        if not state.memory_manager or not state.memory_manager.session_manager:
            raise HTTPException(400, "Session manager not initialized")
        success = await state.memory_manager.session_manager.rename_session(session_id, req.name)
        if not success:
            raise HTTPException(404, "Session not found")
        return {"ok": True}

    @router.delete("/sessions/{session_id}")
    async def delete_session(session_id: str):
        if not state.memory_manager or not state.memory_manager.session_manager:
            raise HTTPException(400, "Session manager not initialized")
        success = await state.memory_manager.session_manager.delete_session(session_id)
        if not success:
            raise HTTPException(404, "Session not found")
        return {"ok": True}

    @router.get("/sessions/{session_id}/messages")
    async def get_session_messages(session_id: str):
        if not state.memory_manager or not state.memory_manager.session_manager:
            raise HTTPException(400, "Session manager not initialized")
        session = await state.memory_manager.session_manager.get_session(session_id)
        if session is None:
            raise HTTPException(404, "Session not found")
        messages = await state.memory_manager.session_manager.load_messages(session_id)
        return {
            "session_id": session_id,
            "messages": [
                {
                    "role": m.role.value,
                    "content": m.content,
                    "tool_call_id": m.tool_call_id,
                    "reasoning_content": m.reasoning_content,
                }
                for m in messages
            ],
        }

    # ===== RAG Endpoints =====

    @router.get("/rag/documents")
    async def list_rag_documents():
        if not state.rag_manager:
            return {"documents": [], "enabled": False}
        docs = await state.rag_manager.list_documents()
        return {"documents": docs, "enabled": True}

    @router.post("/rag/upload")
    async def upload_rag_document(file: UploadFile):
        if not state.rag_manager:
            raise HTTPException(400, "RAG system not enabled")
        if not file.filename:
            raise HTTPException(400, "No file provided")
        ext = Path(file.filename).suffix.lower()
        if ext not in (".txt", ".md", ".markdown"):
            raise HTTPException(400, f"Unsupported file type: {ext}. Supported: .txt, .md")
        content = await file.read()
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)
        try:
            result = await state.rag_manager.upload_document(tmp_path, display_name=file.filename)
            return {"ok": True, "result": result}
        finally:
            tmp_path.unlink(missing_ok=True)

    @router.post("/rag/documents/delete")
    async def delete_rag_document(req: DeleteDocumentRequest):
        if not state.rag_manager:
            raise HTTPException(400, "RAG system not enabled")
        count = await state.rag_manager.remove_document(req.source_path)
        return {"ok": True, "deleted": count}

    @router.get("/rag/status")
    async def get_rag_status():
        if not state.rag_manager:
            return {"enabled": False}
        return {
            "enabled": True,
            "chunk_size": state.rag_manager.chunk_size,
            "chunk_overlap": state.rag_manager.chunk_overlap,
        }

    return router
