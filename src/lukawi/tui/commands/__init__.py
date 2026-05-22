"""Command dispatch system for Lukawi TUI.

Provides a registration-based command system that replaces the monolithic
_handle_command method in app.py with independently testable handler classes.

Exports:
    CommandHandler  - Base class for command handlers
    CommandRegistry - Registration and dispatch hub
    CommandContext  - Typed references to app subsystems
    create_default_registry() - Factory for bootstrapping with built-in commands
    ALL_COMMANDS    - List of all built-in CommandHandler types
"""

from lukawi.tui.commands.factory import ALL_COMMANDS, create_default_registry
from lukawi.tui.commands.handler import CommandContext, CommandHandler, CommandRegistry

__all__ = [
    "CommandHandler",
    "CommandRegistry",
    "CommandContext",
    "create_default_registry",
    "ALL_COMMANDS",
]
