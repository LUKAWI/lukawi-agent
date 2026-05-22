from lukawi.tui.commands.handler import CommandContext, CommandHandler


class QuitCommand(CommandHandler):
    name = "/quit"
    description = "Exit application"
    usage = "/quit"
    category = "general"

    async def execute(self, args: list[str], ctx: CommandContext) -> str:
        ctx.app.exit()
        return ""
