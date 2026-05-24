from lukawi.commands.handler import CommandContext, CommandHandler


class HelpCommand(CommandHandler):
    name = "/help"
    description = "Show help message"
    usage = "/help"
    category = "general"

    async def execute(self, args: list[str], ctx: CommandContext) -> str:
        app = ctx.app
        registry = getattr(app, "command_registry", None)

        if registry is not None:
            commands = registry.list_commands()
            by_category: dict[str, list[CommandHandler]] = {}
            for cmd in commands:
                by_category.setdefault(cmd.category, []).append(cmd)

            lines = ["**Available Commands:**", ""]
            for cat, cmds in sorted(by_category.items()):
                lines.append(f"### {cat.title()}")
                for c in cmds:
                    usage = f" - `{c.usage}`" if c.usage else ""
                    lines.append(f"- `{c.name}{usage}` - {c.description}")
                lines.append("")
            return "\n".join(lines).strip()

        return (
            "**Available Commands:**\n"
            "- `/help` - Show this help\n"
            "- `/clear` - Clear chat history\n"
            "- `/models` - List available models\n"
            "- `/models use <name>` - Switch model\n"
            "- `/skill list` - List all available skills\n"
            "- `/skill load <name>` - Explicitly load a skill into context\n"
            "- `/skill active` - Show currently active skills\n"
            "- `/mcp list` - List MCP servers\n"
            "- `/mcp add <name> <command> [args...]` - Add MCP server\n"
            "- `/mcp remove <name>` - Remove MCP server\n"
            "- `/mcp connect` - Reconnect all MCP servers\n"
            "- `/mcp disconnect` - Disconnect all MCP servers\n"
            "- `/mcp import <file.json>` - Import servers from JSON\n"
            "- `/quit` - Exit application"
        )
