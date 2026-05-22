"""Collapsible sidebar widget — models, sessions, and shortcuts."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from lukawi.tui.events import SidebarToggle

DEFAULT_CSS = """
Sidebar {
    width: 30;
    height: 1fr;
    background: $panel;
    border-right: solid $primary;
    display: none;
}

Sidebar > VerticalScroll {
    padding: 1;
}

Sidebar .sidebar-section-title {
    color: $accent;
    text-style: bold;
    margin: 1 0 0 0;
}

Sidebar .sidebar-section-content {
    color: $foreground-muted;
    margin: 0 0 1 0;
    padding: 0 1;
}
"""


class Sidebar(Widget):
    """Collapsible left sidebar with models, sessions, and shortcuts."""

    collapsed: reactive[bool] = reactive(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="sidebar-scroll"):
            yield Static("Models", classes="sidebar-section-title")
            yield Static(
                "(loading...)", id="sidebar-models", classes="sidebar-section-content"
            )
            yield Static("Sessions", classes="sidebar-section-title")
            yield Static(
                "(no sessions)", id="sidebar-sessions", classes="sidebar-section-content"
            )
            yield Static("Shortcuts", classes="sidebar-section-title")
            yield Static(
                "Ctrl+B  Toggle sidebar\nCtrl+C  Quit\nCtrl+L  Clear chat\nCtrl+M  Models\nCtrl+T  Theme",
                id="sidebar-shortcuts",
                classes="sidebar-section-content",
            )

    def on_sidebar_toggle(self, event: SidebarToggle) -> None:
        self.collapsed = event.visible

    def watch_collapsed(self, value: bool) -> None:
        self.display = not value

    def update_models(self, models: list[str]) -> None:
        """Update the models list."""
        models_widget = self.query_one("#sidebar-models", Static)
        if not models:
            models_widget.update("(no models)")
        else:
            models_widget.update("\n".join(f"• {m}" for m in models))

    def update_sessions(self, sessions: list[str]) -> None:
        """Update the sessions list (placeholder for future)."""
        sessions_widget = self.query_one("#sidebar-sessions", Static)
        if not sessions:
            sessions_widget.update("(no sessions)")
        else:
            sessions_widget.update("\n".join(f"• {s}" for s in sessions))
