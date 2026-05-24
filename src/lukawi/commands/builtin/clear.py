from lukawi.commands.handler import CommandContext, CommandHandler


class ClearCommand(CommandHandler):
    name = "/clear"
    description = "Clear chat history"
    usage = "/clear"
    category = "general"

    async def execute(self, args: list[str], ctx: CommandContext) -> str:
        if ctx.chat_container is not None:
            ctx.chat_container.clear()
            await ctx.chat_container.add_message("Chat cleared.", role="system")
        return "Chat history cleared."
