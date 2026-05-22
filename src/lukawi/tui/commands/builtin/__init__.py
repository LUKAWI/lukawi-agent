"""Built-in command handlers for Lukawi TUI.

Six command handlers covering 14 logical commands:
- HelpCommand   (/help)
- ClearCommand  (/clear)
- ModelsCommand (/models, /models use <name>)
- SkillCommand  (/skill list, /skill active, /skill load <name>)
- McpCommand    (/mcp list|add|remove|connect|disconnect|import)
- QuitCommand   (/quit)
"""

from lukawi.tui.commands.builtin.clear import ClearCommand
from lukawi.tui.commands.builtin.help import HelpCommand
from lukawi.tui.commands.builtin.mcp import McpCommand
from lukawi.tui.commands.builtin.models import ModelsCommand
from lukawi.tui.commands.builtin.quit import QuitCommand
from lukawi.tui.commands.builtin.skill import SkillCommand

__all__ = [
    "HelpCommand",
    "ClearCommand",
    "ModelsCommand",
    "SkillCommand",
    "McpCommand",
    "QuitCommand",
]
