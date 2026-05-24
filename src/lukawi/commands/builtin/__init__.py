"""Built-in command handlers for Lukawi.

Six command handlers covering 14 logical commands:
- HelpCommand   (/help)
- ClearCommand  (/clear)
- ModelsCommand (/models, /models use <name>)
- SkillCommand  (/skill list, /skill active, /skill load <name>)
- McpCommand    (/mcp list|add|remove|connect|disconnect|import)
- QuitCommand   (/quit)
"""

from lukawi.commands.builtin.clear import ClearCommand
from lukawi.commands.builtin.help import HelpCommand
from lukawi.commands.builtin.mcp import McpCommand
from lukawi.commands.builtin.models import ModelsCommand
from lukawi.commands.builtin.quit import QuitCommand
from lukawi.commands.builtin.skill import SkillCommand

__all__ = [
    "HelpCommand",
    "ClearCommand",
    "ModelsCommand",
    "SkillCommand",
    "McpCommand",
    "QuitCommand",
]
