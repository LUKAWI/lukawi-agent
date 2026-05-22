from lukawi.tui.commands.handler import CommandContext, CommandHandler


class ModelsCommand(CommandHandler):
    name = "/models"
    description = "List or switch AI models"
    usage = "/models [use <name>]"
    category = "models"

    async def execute(self, args: list[str], ctx: CommandContext) -> str:
        if not ctx.model_registry:
            return "No model registry configured."

        if args and args[0] == "use" and len(args) >= 2:
            model_name = args[1]
            try:
                ctx.model_registry.use(model_name)
                return f"Switched to model: {model_name}"
            except Exception as e:
                return f"Error switching model: {e}"

        models = ctx.model_registry.list_models()
        if not models:
            return "No models available."

        current = ctx.model_registry.current_name
        lines = ["**Available Models:**"]
        for model in models:
            marker = "x" if model.name == current else " "
            lines.append(f"- [{marker}] {model.name} ({model.provider})")
        return "\n".join(lines)
