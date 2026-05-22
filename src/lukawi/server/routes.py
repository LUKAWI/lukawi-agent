"""REST API routes for Lukawi server."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


class ModelUseRequest(BaseModel):
    name: str


class SkillLoadRequest(BaseModel):
    name: str


class ThemeRequest(BaseModel):
    theme: str


def create_router(state) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/models")
    async def get_models():
        if not state.model_registry:
            return {"models": [], "current": None}
        models = [
            {"name": key, "model": info.name, "provider": info.provider}
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
            state.agent.switch_provider(req.name, provider)
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
            }
            for s in state.skill_loader.list_skills()
        ]
        return {"skills": skills}

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
        import asyncio

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
            "theme": tui.theme if tui else "dark",
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
    async def search_memory(q: str = "", limit: int = 10):
        if not state.memory_manager:
            raise HTTPException(400, "Memory system not initialized")
        if not q.strip():
            return {"memories": []}
        memories = await state.memory_manager.recall(query=q, limit=limit)
        return {
            "memories": [
                {
                    "id": m.id,
                    "content": m.content,
                    "created_at": m.created_at.isoformat(),
                }
                for m in memories
            ]
        }

    @router.post("/memory/clear")
    async def clear_memory():
        if not state.memory_manager:
            raise HTTPException(400, "Memory system not initialized")
        if state.memory_manager.longterm:
            await state.memory_manager.longterm.clear(user_id="default")
        return {"ok": True}

    @router.get("/sessions")
    async def list_sessions():
        if not state.memory_manager or not state.memory_manager.session_manager:
            return {"sessions": []}
        sessions = await state.memory_manager.session_manager.list_sessions()
        return {"sessions": sessions}

    class CreateSessionRequest(BaseModel):
        name: str = "新对话"

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

    return router
