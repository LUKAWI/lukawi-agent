"""Command handler base classes and registry.

Provides the foundation for the command dispatch system:
- CommandContext: typed references to app subsystems
- CommandHandler: base class for all commands
- CommandRegistry: registration and dispatch hub
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CommandContext:
    """Context passed to command handlers — references to app subsystems.

    Uses typing.Any for circular-import-prone types to keep this module
    dependency-free.
    """

    app: Any
    """Reference to the app/subsystem instance."""

    agent: Any
    """The ReActAgent instance for injecting system messages, etc."""

    model_registry: Any | None = None
    """ModelRegistry for listing/switching models."""

    mcp_manager: Any | None = None
    """MCPManager for connecting/disconnecting MCP servers."""

    skill_loader: Any | None = None
    """SkillLoader for listing/loading skills."""

    chat_container: Any | None = None
    """Chat container for displaying command output."""


class CommandHandler:
    """Base class for all command handlers.

    Each handler maps to one primary command name (e.g. "/help").
    Combined commands (/models, /skill, /mcp) check args[0] for subcommand
    routing inside their execute() method.
    """

    name: str = ""
    """Primary command name, e.g. "/help", "/models"."""

    description: str = ""
    """Short description shown in /help output."""

    usage: str = ""
    """Usage string, e.g. "/models use <name>"."""

    category: str = "general"
    """Category for grouping in help output."""

    async def execute(self, args: list[str], ctx: CommandContext) -> str:
        """Execute the command.

        Args:
            args: Positional arguments after the command name.
            ctx: CommandContext with app subsystem references.

        Returns:
            Text to display in the chat (markdown-formatted).
        """
        raise NotImplementedError


class CommandRegistry:
    """Registration-based command dispatcher.

    Usage:
        registry = CommandRegistry()
        registry.register(HelpCommand())
        response = await registry.dispatch("/help", [], ctx)
    """

    def __init__(self) -> None:
        self._handlers: dict[str, CommandHandler] = {}

    def register(self, handler: CommandHandler) -> None:
        """Register a command handler.

        If a handler with the same name already exists, it is replaced.
        """
        self._handlers[handler.name] = handler

    def get(self, name: str) -> CommandHandler | None:
        """Get a handler by command name."""
        return self._handlers.get(name)

    def list_commands(self) -> list[CommandHandler]:
        """Return all registered command handlers."""
        return list(self._handlers.values())

    async def dispatch(
        self, command: str, args: list[str], ctx: CommandContext
    ) -> str:
        """Dispatch a command to its handler.

        Args:
            command: The command name (e.g. "/help", "/models", "/skill").
            args: Positional arguments after the command name.
            ctx: CommandContext with app references.

        Returns:
            Response text (markdown-formatted) to display in chat.
        """
        handler = self._handlers.get(command)
        if handler is None:
            return f"Unknown command: {command}. Type /help for available commands."
        return await handler.execute(args, ctx)
