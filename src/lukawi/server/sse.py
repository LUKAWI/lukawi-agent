"""SSE chat streaming endpoint — streams agent events to the frontend."""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from lukawi.agent.core import AgentEventType
from lukawi.skills.executor import match_triggers, build_skill_injection
from lukawi.llm.base import Message, MessageRole

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str
    session_id: str = ""


def create_sse_router(state) -> APIRouter:
    router = APIRouter()

    @router.post("/api/chat")
    async def chat(req: ChatRequest, session_id: str = ""):
        if not req.session_id and session_id:
            req.session_id = session_id
        # Fallback to last active session if no session_id provided
        if not req.session_id and hasattr(state, "last_session_id") and state.last_session_id:
            req.session_id = state.last_session_id
        if not state.agent:
            async def error_stream():
                yield "event: error\ndata: {\"error\":\"Agent not initialized\"}\n\n"
                yield "event: done\ndata: {}\n\n"
            return StreamingResponse(error_stream(), media_type="text/event-stream")

        async def event_stream():
            message = req.message.strip()

            # Resolve session: auto-create if not provided
            session_id = req.session_id
            session_manager = None
            if state.memory_manager and state.memory_manager.session_manager:
                session_manager = state.memory_manager.session_manager
                if not session_id:
                    session = await session_manager.create_session()
                    session_id = session.id
                else:
                    existing = await session_manager.get_session(session_id)
                    if existing is None:
                        session = await session_manager.create_session()
                        session_id = session.id

            assistant_reply = ""

            # Per-request flag to attach session_id only once
            session_sent = False

            # Handle slash commands
            if message.startswith("/"):
                try:
                    result = await _dispatch_command(message, state)
                    yield f"event: answer\ndata: {json.dumps({'content': result})}\n\n"
                except Exception as e:
                    yield f"event: error\ndata: {json.dumps({'error': f'Command failed: {e}'})}\n\n"
                    import traceback
                    import sys
                    print(traceback.format_exc(), file=sys.stderr)
                yield "event: done\ndata: {}\n\n"
                return

            # Skill trigger detection — only check user-selected skills
            if state.skill_loader and state.selected_skills:
                enabled = [
                    s for s in state.skill_loader.list_skills()
                    if s.name in state.selected_skills
                ]
                matched = match_triggers(message, enabled)
                for skill in matched:
                    if skill.name not in state.active_skills:
                        injection = build_skill_injection(skill)
                        state.active_skills[skill.name] = injection
                        state.agent.inject_system_message(injection)

            try:
                # Load history from session manager
                history: list[Message] = []
                if session_manager and session_id:
                    history = await session_manager.load_messages(session_id)

                async for event in state.agent.run(message, history=history, session_id=session_id):
                    event_type_map = {
                        AgentEventType.THINKING: "thinking",
                        AgentEventType.STREAMING_TOKEN: "answer",
                        AgentEventType.TOOL_CALL: "tool_call",
                        AgentEventType.TOOL_RESULT: "tool_result",
                        AgentEventType.FINAL_ANSWER: "answer",
                        AgentEventType.ERROR: "error",
                    }
                    sse_type = event_type_map.get(event.type)
                    if sse_type is None:
                        continue

                    payload = dict(event.data)

                    if event.type == AgentEventType.STREAMING_TOKEN:
                        assistant_reply += payload.get("content", "")
                    elif event.type == AgentEventType.FINAL_ANSWER:
                        if not assistant_reply:
                            assistant_reply = payload.get("content", "")
                        else:
                            # Content already streamed via STREAMING_TOKEN events
                            continue

                    # Attach session_id to first event so frontend knows the session
                    if event.type == AgentEventType.THINKING and not session_sent:
                        payload["session_id"] = session_id
                        session_sent = True

                    # Normalize tool_result to always have status + result as str
                    if event.type == AgentEventType.TOOL_RESULT:
                        result_data = payload.get("result")
                        if result_data is not None:
                            if hasattr(result_data, "status"):
                                payload["status"] = result_data.status.value
                            if hasattr(result_data, "result"):
                                payload["result"] = str(result_data.result)[:2000] if result_data.result else ""
                            else:
                                payload["result"] = str(result_data)[:2000]
                        else:
                            payload["result"] = ""

                    yield f"event: {sse_type}\ndata: {json.dumps(payload, default=str)}\n\n"
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                import traceback
                import sys
                print(traceback.format_exc(), file=sys.stderr)

            # Persist messages to session manager
            if session_manager and session_id and assistant_reply:
                msgs_to_save = [
                    Message(role=MessageRole.USER, content=message),
                    Message(role=MessageRole.ASSISTANT, content=assistant_reply),
                ]
                try:
                    await session_manager.save_messages(session_id, msgs_to_save)
                except Exception as e:
                    logger.warning("Failed to save session messages: %s", e)

                if state.memory_manager:
                    await state.memory_manager.save_conversation(
                        summary=assistant_reply[:200],
                        user_id="default",
                        session_id=session_id,
                    )

            # Track this as the last active session for fallback
            if session_id:
                state.last_session_id = session_id

            yield "event: done\ndata: {}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    return router


async def _dispatch_command(message: str, state) -> str:
    """Reuse the existing command system with a server context."""
    from lukawi.commands import create_default_registry
    from lukawi.commands.handler import CommandContext

    parts = message[1:].strip().split()
    command = parts[0]
    args = parts[1:] if len(parts) > 1 else []

    registry = create_default_registry()
    ctx = CommandContext(
        app=state,
        agent=state.agent,
        model_registry=state.model_registry,
        mcp_manager=state.mcp_manager,
        skill_loader=state.skill_loader,
        chat_container=None,
    )
    return await registry.dispatch(f"/{command}", args, ctx)
