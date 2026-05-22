"""Chat container — composes MessageList + ChatInput into a vertical chat panel."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget

from lukawi.tui.widgets.message_list import MessageList, StreamingMessage, ToolCallMessage
from lukawi.tui.widgets.input import ChatInput


class ChatContainer(Widget):
    """Chat panel wrapping a vertical layout of message list and input."""

    DEFAULT_CSS = """
    ChatContainer {
        height: 1fr;
        width: 1fr;
    }

    #chat-inner {
        height: 1fr;
    }

    #chat-inner > MessageList {
        height: 1fr;
    }

    #chat-inner > ChatInput {
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="chat-inner"):
            yield MessageList(id="message-list")
            yield ChatInput(id="chat-input")

    @property
    def message_list(self) -> MessageList:
        return self.query_one("#message-list", MessageList)

    @property
    def input_widget(self) -> ChatInput:
        return self.query_one("#chat-input", ChatInput)

    async def add_message(self, content: str, role: str = "user") -> StreamingMessage:
        return await self.message_list.add_message(content, role)

    async def add_tool_message(
        self,
        tool_name: str,
        params: dict | None = None,
        result: str = "",
        status: str = "running",
    ) -> ToolCallMessage:
        return await self.message_list.add_tool_message(tool_name, params, result, status)

    def clear(self) -> None:
        self.message_list.clear()

    def focus_input(self) -> None:
        self.input_widget.focus_input()
