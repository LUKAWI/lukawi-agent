"""TUI event/message types.

All messages in this module inherit from ``textual.message.Message``
and are posted by widgets then handled by the main ``LukawiApp``.
"""

from __future__ import annotations

from textual.message import Message

__all__ = [
    "AgentStreamEvent",
    "ChatSubmitted",
    "CommandSubmitted",
    "SidebarToggle",
    "StatusUpdate",
    "ThemeChanged",
]

_VALID_STREAM_EVENTS = frozenset({
    "thinking",
    "tool_call",
    "tool_result",
    "streaming",
    "final_answer",
    "error",
    "done",
})


class ChatSubmitted(Message):
    """User typed a message and pressed Enter / Send."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text


class CommandSubmitted(Message):
    """User typed a line starting with ``/``."""

    def __init__(self, command: str, args: list[str]) -> None:
        super().__init__()
        self.command = command
        self.args = args


class StatusUpdate(Message):
    """Periodic status-bar refresh."""

    def __init__(
        self,
        model: str,
        tokens: int,
        mcp_connected: int,
        mcp_total: int,
        active_skills: int,
    ) -> None:
        super().__init__()
        self.model = model
        self.tokens = tokens
        self.mcp_connected = mcp_connected
        self.mcp_total = mcp_total
        self.active_skills = active_skills


class ThemeChanged(Message):
    """User switched themes via command or shortcut."""

    def __init__(self, theme_name: str) -> None:
        super().__init__()
        self.theme_name = theme_name


class SidebarToggle(Message):
    """Sidebar visibility was toggled."""

    def __init__(self, visible: bool) -> None:
        super().__init__()
        self.visible = visible


class AgentStreamEvent(Message):
    """Streaming event from the agent loop.

    Parameters
    ----------
    event_type:
        One of ``"thinking"``, ``"tool_call"``, ``"tool_result"``,
        ``"streaming"``, ``"final_answer"``, ``"error"``, ``"done"``.
    data:
        Payload associated with the event (structure varies by type).
    """

    def __init__(self, event_type: str, data: dict) -> None:
        super().__init__()
        if event_type not in _VALID_STREAM_EVENTS:
            raise ValueError(
                f"Invalid AgentStreamEvent type {event_type!r}. "
                f"Must be one of {sorted(_VALID_STREAM_EVENTS)}"
            )
        self.event_type = event_type
        self.data = data
