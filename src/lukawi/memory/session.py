"""Session memory for conversation history."""

from __future__ import annotations

from lukawi.llm.base import Message, MessageRole


class SessionMemory:
    """In-memory session memory for conversation history."""

    def __init__(self, max_messages: int = 100) -> None:
        self.max_messages = max_messages
        self._messages: list[Message] = []

    def add(self, message: Message) -> None:
        self._messages.append(message)

        if len(self._messages) > self.max_messages:
            if self._messages[0].role == MessageRole.SYSTEM:
                system_msg = self._messages[0]
                self._messages = [system_msg] + self._messages[-(self.max_messages - 1):]
            else:
                self._messages = self._messages[-self.max_messages:]

    def get_history(self, limit: int | None = None) -> list[Message]:
        if limit is None:
            return list(self._messages)
        return self._messages[-limit:]

    def get_context_window(self, max_tokens: int = 4000) -> list[Message]:
        char_budget = max_tokens * 4
        total_chars = 0
        result: list[Message] = []

        for msg in reversed(self._messages):
            msg_chars = len(msg.content or "") + 10
            if total_chars + msg_chars > char_budget and result:
                break
            result.append(msg)
            total_chars += msg_chars

        result.reverse()
        return result

    def clear(self) -> None:
        self._messages.clear()

    @property
    def message_count(self) -> int:
        return len(self._messages)

    def __len__(self) -> int:
        return len(self._messages)
