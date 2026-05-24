"""Command dispatch system for Lukawi.

Provides a registration-based command system with independently testable
handler classes.

Exports:
    CommandHandler  - Base class for command handlers
    CommandRegistry - Registration and dispatch hub
    CommandContext  - Typed references to app subsystems
    create_default_registry() - Factory for bootstrapping with built-in commands
    ALL_COMMANDS    - List of all built-in CommandHandler types
"""

from lukawi.commands.factory import ALL_COMMANDS, create_default_registry
from lukawi.commands.handler import CommandContext, CommandHandler, CommandRegistry

__all__ = [
    "CommandHandler",
    "CommandRegistry",
    "CommandContext",
    "create_default_registry",
    "ALL_COMMANDS",
]
