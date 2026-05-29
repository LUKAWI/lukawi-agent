"""Memory manager orchestrating session and long-term memory."""

from __future__ import annotations

from datetime import UTC, datetime

from lukawi.llm.base import Message, MessageRole
from lukawi.memory.longterm import LongTermMemory, Memory
from lukawi.memory.session import SessionMemory
from lukawi.memory.session_manager import SessionManager
from lukawi.rag.manager import RAGManager


class MemoryManager:
    """Unified memory manager combining session and long-term memory."""

    def __init__(
        self,
        db_path: str = ":memory:",
        session_max_messages: int = 100,
        longterm_enabled: bool = True,
        rag_manager: RAGManager | None = None,
    ) -> None:
        self.session = SessionMemory(max_messages=session_max_messages)
        self.rag = rag_manager
        self.longterm = (
            LongTermMemory(db_path=db_path)
            if (longterm_enabled and rag_manager is None)
            else None
        )
        self.longterm_enabled = longterm_enabled
        self.session_manager = SessionManager(db_path=db_path)

    async def initialize(self) -> None:
        if self.rag:
            await self.rag.initialize()
        elif self.longterm:
            await self.longterm.initialize()
        await self.session_manager.initialize()

    async def close(self) -> None:
        if self.rag:
            await self.rag.close()
        elif self.longterm:
            await self.longterm.close()
        await self.session_manager.close()

    def add_message(self, message: Message) -> None:
        self.session.add(message)

    async def save_conversation(
        self,
        user_id: str = "default",
        agent_id: str = "lukawi",
        summary: str | None = None,
        session_id: str | None = None,
    ) -> str | None:
        if summary is None:
            messages = self.session.get_history(limit=10)
            summary = self._generate_summary(messages)

        if self.rag:
            return await self.rag.index_conversation(
                content=summary,
                user_id=user_id,
                metadata={"agent_id": agent_id, "type": "conversation_summary"},
                session_id=session_id,
            )

        if self.longterm:
            return await self.longterm.add(
                content=summary,
                metadata={"type": "conversation_summary"},
                user_id=user_id,
                agent_id=agent_id,
            )

        return None

    async def recall(
        self,
        query: str,
        user_id: str = "default",
        limit: int = 5,
        session_id: str | None = None,
        source_paths: list[str] | None = None,
    ) -> list[Memory]:
        if self.rag:
            results = await self.rag.search(
                query=query, user_id=user_id, limit=limit, session_id=session_id, source_paths=source_paths
            )
            return [self._search_result_to_memory(r) for r in results]

        if self.longterm:
            return await self.longterm.search(
                query=query, user_id=user_id, limit=limit
            )

        return []

    def get_context(self, max_tokens: int = 4000) -> list[Message]:
        return self.session.get_context_window(max_tokens)

    def clear_session(self) -> None:
        self.session.clear()

    async def clear_all(self, user_id: str = "default") -> None:
        if self.longterm:
            await self.longterm.clear(user_id)
        self.clear_session()

    def _generate_summary(self, messages: list[Message]) -> str:
        if not messages:
            return "Empty conversation"

        user_msgs = [m for m in messages if m.role == MessageRole.USER]
        assistant_msgs = [m for m in messages if m.role == MessageRole.ASSISTANT]

        parts: list[str] = []
        if user_msgs:
            parts.append(f"User asked {len(user_msgs)} questions")
        if assistant_msgs:
            parts.append(f"Assistant provided {len(assistant_msgs)} responses")

        body = ". ".join(parts) if parts else "No exchanges"
        return f"Conversation: {body}"

    def _search_result_to_memory(self, r) -> Memory:
        created_str = r.metadata.get("created_at")
        try:
            created_at = datetime.fromisoformat(created_str) if created_str else datetime.now(UTC)
        except (ValueError, TypeError):
            created_at = datetime.now(UTC)
        return Memory(
            id=r.chunk_id,
            content=r.content,
            metadata=r.metadata,
            user_id=r.metadata.get("user_id", "default"),
            agent_id=r.metadata.get("agent_id", "lukawi"),
            created_at=created_at,
            updated_at=created_at,
            score=r.score,
        )
