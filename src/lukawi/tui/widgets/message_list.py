"""Streaming-aware message list widget.

Replaces the original ``ChatContainer`` + ``ChatMessage`` widgets with
incremental-token support and tool-call visibility.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.css.query import NoMatches
from textual.widget import Widget
from textual.widgets import Static

DEFAULT_CSS = """
MessageList {
    height: 1fr;
}

MessageList VerticalScroll {
    padding: 0 1;
}

StreamingMessage {
    margin: 1 0;
    padding: 1;
    height: auto;
}

StreamingMessage.msg-user {
    background: $surface;
    border-left: solid $accent;
}

StreamingMessage.msg-assistant {
    background: $panel;
    border-left: solid $success;
}

StreamingMessage.msg-system {
    background: $surface-darken-1;
    border-left: solid $warning;
}

StreamingMessage.msg-tool {
    background: $surface-darken-2;
    border-left: solid $secondary;
}

.msg-role {
    color: $foreground-muted;
    text-style: bold;
    margin-bottom: 1;
}

.msg-content {
    width: 100%;
}

ToolCallMessage {
    margin: 1 0;
    padding: 1;
    background: $panel-darken-1;
    border-left: solid $secondary;
    height: auto;
}

.tool-name {
    color: $accent;
    text-style: bold;
}

.tool-params {
    color: $foreground-muted;
    margin: 1 0;
}

.tool-result {
    color: $success;
}
"""


class StreamingMessage(Widget):
    """A chat message that supports incremental token appends."""

    role: str
    content: str

    def __init__(self, message: str = "", role: str = "assistant", **kwargs) -> None:
        super().__init__(**kwargs)
        self.role = role
        self.content = message
        self.add_class(f"msg-{role}")

    def compose(self) -> ComposeResult:
        role_labels = {
            "user": "👤 You",
            "assistant": "🤖 Assistant",
            "system": "⚙️ System",
            "tool": "🔧 Tool",
        }
        label = role_labels.get(self.role, self.role)
        yield Static(label, classes="msg-role")
        yield Static(self._render_content(), classes="msg-content")

    def _render_content(self) -> str:
        return self.content if self.content else "..."

    def append_token(self, token: str) -> None:
        self.content += token
        try:
            content_widget = self.query_one(".msg-content", Static)
        except NoMatches:
            return
        content_widget.update(self._render_content())

    def update_content(self, content: str) -> None:
        self.content = content
        try:
            content_widget = self.query_one(".msg-content", Static)
        except NoMatches:
            return
        content_widget.update(self._render_content())


class ToolCallMessage(Widget):
    tool_name: str
    params: dict
    result: str
    status: str

    def __init__(
        self,
        tool_name: str = "",
        params: dict | None = None,
        result: str = "",
        status: str = "running",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.params = params or {}
        self.result = result
        self.status = status
        self.add_class(f"tool-{status}")

    def compose(self) -> ComposeResult:
        yield Static(f"🔧 {self.tool_name}", classes="tool-name")
        if self.params:
            yield Static(str(self.params)[:200], classes="tool-params")
        yield Static(str(self.result)[:500] if self.result else "", classes="tool-result")

    def update_result(self, result: str, status: str = "success") -> None:
        self.result = result
        self.status = status
        try:
            result_widget = self.query_one(".tool-result", Static)
        except NoMatches:
            return
        result_widget.update(str(result)[:500])


class MessageList(Widget):
    max_messages: int

    def __init__(self, max_messages: int = 100, **kwargs) -> None:
        super().__init__(**kwargs)
        self.max_messages = max_messages

    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="message-scroll")

    async def add_message(self, content: str, role: str = "user") -> StreamingMessage:
        """Add a new message and return it for continued token streaming."""
        msg = StreamingMessage(content, role=role)
        scroll = self.query_one("#message-scroll", VerticalScroll)
        await scroll.mount(msg)
        self._trim_old_messages()
        self._scroll_to_bottom()
        return msg

    async def add_tool_message(
        self,
        tool_name: str,
        params: dict | None = None,
        result: str = "",
        status: str = "running",
    ) -> ToolCallMessage:
        msg = ToolCallMessage(tool_name, params, result, status)
        scroll = self.query_one("#message-scroll", VerticalScroll)
        await scroll.mount(msg)
        self._scroll_to_bottom()
        return msg

    def clear(self) -> None:
        scroll = self.query_one("#message-scroll", VerticalScroll)
        scroll.remove_children()

    def _trim_old_messages(self) -> None:
        scroll = self.query_one("#message-scroll", VerticalScroll)
        children = list(scroll.children)
        excess = len(children) - self.max_messages
        for child in children[:excess]:
            child.remove()

    def _scroll_to_bottom(self) -> None:
        scroll = self.query_one("#message-scroll", VerticalScroll)
        scroll.scroll_end(animate=False)
