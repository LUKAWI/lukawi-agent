"""Chat input widget with history, command autocomplete, and multi-line support.

Posts ``ChatSubmitted`` / ``CommandSubmitted`` from ``lukawi.tui.events``
instead of the old inline message classes.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, Input, Static

from lukawi.tui.events import ChatSubmitted, CommandSubmitted

if TYPE_CHECKING:
    from lukawi.tui.commands.handler import CommandRegistry


class ChatInput(Widget):
    """Chat input widget with history, autocomplete, and command support.

    Parameters
    ----------
    command_registry:
        Optional :class:`CommandRegistry` for ``/`` autocomplete.
    """

    DEFAULT_CSS = """
    ChatInput {
        height: auto;
        padding: 0 1;
    }

    #autocomplete-popup {
        background: $panel;
        color: $foreground-muted;
        padding: 0 1;
        margin-bottom: 1;
    }

    #autocomplete-popup.hidden {
        display: none;
    }

    #input-row Input {
        width: 1fr;
    }

    #input-row Button {
        min-width: 10;
        margin-left: 1;
    }
    """

    def __init__(
        self,
        command_registry: CommandRegistry | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.history: deque[str] = deque(maxlen=100)
        self._history_pos: int = -1
        self._current_input: str = ""
        self.command_registry = command_registry
        self._showing_autocomplete: bool = False

    def compose(self) -> ComposeResult:
        with Vertical(id="input-area"):
            yield Static("", id="autocomplete-popup", classes="hidden")
            with Horizontal(id="input-row"):
                yield Input(
                    placeholder="Type a message or /command...",
                    id="chat-input",
                )
                yield Button("Send", id="send-btn", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-btn":
            self._submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._submit()

    def _submit(self) -> None:
        inp = self.query_one("#chat-input", Input)
        text = inp.value.strip()

        if not text:
            return

        self.history.append(text)
        self._history_pos = -1
        self._current_input = ""

        inp.value = ""
        self._hide_autocomplete()

        if text.startswith("/"):
            parts = text[1:].split()
            command = "/" + parts[0]
            args = parts[1:] if len(parts) > 1 else []
            self.post_message(CommandSubmitted(command, args))
        else:
            self.post_message(ChatSubmitted(text))

    def on_key(self, event: events.Key) -> None:
        input_widget = self.query_one("#chat-input", Input)

        if event.key == "escape":
            if self._showing_autocomplete:
                self._hide_autocomplete()
                event.stop()
                event.prevent_default()
            return

        if event.key == "enter":
            if self._shift_held(event):
                input_widget.value += "\n"
                input_widget.action_end()
                event.stop()
                event.prevent_default()
            return

        if event.key not in ("up", "down"):
            return

        if not input_widget.has_focus:
            return

        if event.key == "up":
            if self.history and self._history_pos < len(self.history) - 1:
                if self._history_pos == -1:
                    self._current_input = input_widget.value
                self._history_pos += 1
                input_widget.value = self.history[-(self._history_pos + 1)]
            event.stop()
            event.prevent_default()
        elif event.key == "down":
            if self._history_pos > 0:
                self._history_pos -= 1
                input_widget.value = self.history[-(self._history_pos + 1)]
            elif self._history_pos == 0:
                self._history_pos = -1
                input_widget.value = self._current_input
            event.stop()
            event.prevent_default()


    def on_input_changed(self, event: Input.Changed) -> None:
        if self.command_registry and event.value.startswith("/"):
            self._show_autocomplete(event.value)
        else:
            self._hide_autocomplete()

    def _show_autocomplete(self, value: str) -> None:
        commands = self.command_registry.list_commands()
        matching = [c for c in commands if c.name.startswith(value)]
        if matching:
            popup = self.query_one("#autocomplete-popup", Static)
            popup.update("\n".join(c.name for c in matching[:5]))
            popup.remove_class("hidden")
            self._showing_autocomplete = True

    def _hide_autocomplete(self) -> None:
        popup = self.query_one("#autocomplete-popup", Static)
        popup.add_class("hidden")
        self._showing_autocomplete = False


    @staticmethod
    def _shift_held(event: events.Key) -> bool:
        """Detect whether Shift was held during this key event.

        Textual's ``events.Key`` does not expose modifier state directly.
        When Textual adds modifier support this method can be updated to
        check ``event.modifiers`` or similar.
        """
        # Future: return bool(event.modifiers & Modifier.SHIFT)
        return False

    def focus_input(self) -> None:
        """Focus the input widget."""
        self.query_one("#chat-input", Input).focus()
