"""Factory for creating a fully-populated CommandRegistry."""

from __future__ import annotations

from lukawi.commands.builtin import (
    ClearCommand,
    HelpCommand,
    McpCommand,
    ModelsCommand,
    QuitCommand,
    SkillCommand,
)
from lukawi.commands.handler import CommandHandler, CommandRegistry


ALL_COMMANDS: list[type[CommandHandler]] = [
    HelpCommand,
    ClearCommand,
    ModelsCommand,
    SkillCommand,
    McpCommand,
    QuitCommand,
]


def create_default_registry() -> CommandRegistry:
    registry = CommandRegistry()
    registry.register(HelpCommand())
    registry.register(ClearCommand())
    registry.register(ModelsCommand())
    registry.register(SkillCommand())
    registry.register(McpCommand())
    registry.register(QuitCommand())
    return registry
