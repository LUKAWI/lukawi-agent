"""Status bar widget — single-row display of session state.

Subscribes to ``StatusUpdate`` messages for reactive updates
of model name, token count, MCP connection status, and active skills.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from lukawi.tui.events import StatusUpdate


class StatusBar(Widget):
    """Single-row status bar showing session state."""

    model_name: reactive[str] = reactive("")
    token_count: reactive[int] = reactive(0)
    mcp_connected: reactive[int] = reactive(0)
    mcp_total: reactive[int] = reactive(0)
    active_skills: reactive[int] = reactive(0)

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: $panel;
        color: $foreground-muted;
        padding: 0 1;
    }
    StatusBar Static {
        width: 100%;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Static(id="status-text")

    def watch_model_name(self, value: str) -> None:
        self._refresh()

    def watch_token_count(self, value: int) -> None:
        self._refresh()

    def watch_mcp_connected(self, value: int) -> None:
        self._refresh()

    def watch_mcp_total(self, value: int) -> None:
        self._refresh()

    def watch_active_skills(self, value: int) -> None:
        self._refresh()

    def on_status_update(self, event: StatusUpdate) -> None:
        self.model_name = event.model
        self.token_count = event.tokens
        self.mcp_connected = event.mcp_connected
        self.mcp_total = event.mcp_total
        self.active_skills = event.active_skills

    def _refresh(self) -> None:
        status = self.query_one("#status-text", Static)
        parts = []
        if self.model_name:
            parts.append(f"[Model: {self.model_name}]")
        parts.append(f"[Tokens: {self.token_count}]")
        if self.mcp_total > 0:
            parts.append(f"[MCP: {self.mcp_connected}/{self.mcp_total} connected]")
        if self.active_skills > 0:
            parts.append(f"[Skills: {self.active_skills} active]")
        status.update("  ".join(parts))
