"""Memory tools for LLM to query and save long-term memories."""

from __future__ import annotations

import json

from lukawi.tools.base import (
    ToolDefinition,
    ToolResult,
    ToolParameter,
    ToolParameterType,
)
from lukawi.tools.registry import ToolRegistry
from lukawi.memory.manager import MemoryManager


MEMORY_RECALL_TOOL = ToolDefinition(
    name="memory_recall",
    description="Search through past conversation memories. Use this to remember user preferences, past topics, or any information from previous conversations.",
    parameters=[
        ToolParameter(
            name="query",
            type=ToolParameterType.STRING,
            description="Keywords or phrase to search for in past memories",
        ),
        ToolParameter(
            name="limit",
            type=ToolParameterType.INTEGER,
            description="Maximum number of memories to return",
            required=False,
            default=5,
        ),
    ],
    category="memory",
    tags=["memory", "recall", "search", "history"],
)

MEMORY_SAVE_TOOL = ToolDefinition(
    name="memory_save",
    description="Save important information about the user or conversation to long-term memory so it can be recalled in future conversations.",
    parameters=[
        ToolParameter(
            name="content",
            type=ToolParameterType.STRING,
            description="The information to remember. Be specific and include key details about the user, their preferences, or important facts.",
        ),
        ToolParameter(
            name="metadata_json",
            type=ToolParameterType.STRING,
            description="Optional JSON string with additional metadata (e.g., {'topic': 'preference'})",
            required=False,
            default="{}",
        ),
    ],
    category="memory",
    tags=["memory", "save", "store"],
)


def register_memory_tools(registry: ToolRegistry, memory_manager: MemoryManager | None = None) -> None:
    """Register memory tools with the given registry.

    Args:
        registry: ToolRegistry instance
        memory_manager: Optional MemoryManager instance (if None, tools return errors)
    """

    async def memory_recall_handler(query: str, limit: int = 5) -> ToolResult:
        """Search through session context first, then long-term memory.

        Args:
            query: Keywords or phrase to search for
            limit: Maximum number of memories to return

        Returns:
            ToolResult with matching memories
        """
        if memory_manager is None:
            return ToolResult.error("Memory manager not available")

        try:
            results: list[dict] = []
            query_lower = query.lower()

            # Phase 1: Search session context (current conversation messages)
            session_manager = getattr(memory_manager, "session_manager", None)
            if session_manager:
                session_messages = getattr(session_manager, "_messages_cache", {})
                for session_id, messages in session_messages.items():
                    for msg in messages:
                        if msg.content and query_lower in msg.content.lower():
                            results.append({
                                "type": "session",
                                "session_id": session_id,
                                "role": msg.role.value if hasattr(msg.role, "value") else str(msg.role),
                                "content": msg.content,
                                "tool_call_id": getattr(msg, "tool_call_id", None),
                            })

            # Phase 2: If nothing found in session, search long-term memory
            if not results and memory_manager.longterm:
                memories = await memory_manager.recall(query=query, limit=limit)
                for m in memories:
                    results.append({
                        "type": "longterm",
                        "id": m.id,
                        "content": m.content,
                        "metadata": m.metadata,
                        "user_id": m.user_id,
                        "agent_id": m.agent_id,
                        "created_at": m.created_at.isoformat() if hasattr(m.created_at, "isoformat") else str(m.created_at),
                        "updated_at": m.updated_at.isoformat() if hasattr(m.updated_at, "isoformat") else str(m.updated_at),
                    })

            return ToolResult.success(
                result=results[:limit],
                metadata={"count": len(results[:limit]), "source": "session" if results and results[0].get("type") == "session" else "longterm"},
            )
        except Exception as e:
            return ToolResult.error(f"Memory recall failed: {e}")

    async def memory_save_handler(content: str, metadata_json: str = "{}") -> ToolResult:
        """Save important information to long-term memory.

        Args:
            content: The information to remember
            metadata_json: Optional JSON string with additional metadata

        Returns:
            ToolResult with memory_id on success
        """
        if memory_manager is None:
            return ToolResult.error("Memory manager not available")

        try:
            metadata: dict = json.loads(metadata_json)
        except json.JSONDecodeError as e:
            return ToolResult.error(f"Invalid metadata JSON: {e}")

        try:
            memory_id = await memory_manager.save_conversation(
                summary=content,
                user_id="default",
            )
            if memory_id is None:
                return ToolResult.error("Memory manager returned no ID (longterm disabled?)")

            return ToolResult.success(
                result={
                    "message": "Memory saved successfully",
                    "memory_id": memory_id,
                    "metadata": metadata,
                },
            )
        except Exception as e:
            return ToolResult.error(f"Memory save failed: {e}")

    registry.register(MEMORY_RECALL_TOOL, memory_recall_handler)
    registry.register(MEMORY_SAVE_TOOL, memory_save_handler)