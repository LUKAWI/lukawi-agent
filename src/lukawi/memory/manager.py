"""Memory manager orchestrating session and long-term memory."""

from __future__ import annotations


from lukawi.memory.session import SessionMemory
from lukawi.memory.longterm import LongTermMemory, Memory
from lukawi.memory.session_manager import SessionManager
from lukawi.llm.base import Message, MessageRole


class MemoryManager:
    """Unified memory manager combining session and long-term memory."""

    def __init__(
        self,
        db_path: str = ":memory:",
        session_max_messages: int = 100,
        longterm_enabled: bool = True,
    ) -> None:
        self.session = SessionMemory(max_messages=session_max_messages)
        self.longterm = LongTermMemory(db_path=db_path) if longterm_enabled else None
        self.longterm_enabled = longterm_enabled
        self.session_manager = SessionManager(db_path=db_path)

    async def initialize(self) -> None:
        if self.longterm:
            await self.longterm.initialize()
        await self.session_manager.initialize()

    async def close(self) -> None:
        if self.longterm:
            await self.longterm.close()
        await self.session_manager.close()

    def add_message(self, message: Message) -> None:
        self.session.add(message)

    async def save_conversation(
        self,
        user_id: str = "default",
        agent_id: str = "lukawi",
        summary: str | None = None,
    ) -> str | None:
        if not self.longterm:
            return None

        if summary is None:
            messages = self.session.get_history(limit=10)
            summary = self._generate_summary(messages)

        return await self.longterm.add(
            content=summary,
            metadata={"type": "conversation_summary"},
            user_id=user_id,
            agent_id=agent_id,
        )

    async def recall(
        self,
        query: str,
        user_id: str = "default",
        limit: int = 5,
    ) -> list[Memory]:
        if not self.longterm:
            return []

        return await self.longterm.search(query=query, user_id=user_id, limit=limit)

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