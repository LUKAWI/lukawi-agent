from lukawi.skills.executor import build_skill_injection
from lukawi.tui.commands.handler import CommandContext, CommandHandler


class SkillCommand(CommandHandler):
    name = "/skill"
    description = "Manage agent skills"
    usage = "/skill <list|active|load <name>>"
    category = "skills"

    async def execute(self, args: list[str], ctx: CommandContext) -> str:
        if not args:
            return "Usage: `/skill list`, `/skill active`, `/skill load <name>`"

        sub = args[0]

        if sub == "list":
            return await self._list(ctx)
        elif sub == "active":
            return await self._active(ctx)
        elif sub == "load" and len(args) >= 2:
            return await self._load(args[1], ctx)
        else:
            return "Usage: `/skill list`, `/skill active`, `/skill load <name>`"

    async def _list(self, ctx: CommandContext) -> str:
        if not ctx.skill_loader:
            return "Skill system not initialized."
        skills = ctx.skill_loader.list_skills()
        if not skills:
            return "No skills loaded."
        active_skills: dict = getattr(ctx.app, "active_skills", {})
        lines = ["**Available Skills:**"]
        for s in skills:
            tags = ", ".join(s.triggers[:5]) if s.triggers else "none"
            marker = "+" if s.name in active_skills else " "
            lines.append(f"- [{marker}] `{s.name}` triggers=[{tags}]")
        lines.append(
            f"\n_Total: {len(skills)} skills, {len(active_skills)} active_"
        )
        return "\n".join(lines)

    async def _active(self, ctx: CommandContext) -> str:
        active_skills: dict = getattr(ctx.app, "active_skills", {})
        if not active_skills:
            return "No skills are currently active."
        lines = ["**Active Skills:**"]
        for name, instr in active_skills.items():
            lines.append(f"- `{name}`: {instr[:100]}...")
        return "\n".join(lines)

    async def _load(self, skill_name: str, ctx: CommandContext) -> str:
        if not ctx.skill_loader:
            return "Skill system not initialized."
        skill = ctx.skill_loader.get_skill(skill_name)
        if not skill:
            return (
                f"Skill '{skill_name}' not found. "
                "Use `/skill list` to see available skills."
            )
        injection = build_skill_injection(skill)
        active_skills: dict = getattr(ctx.app, "active_skills", {})
        active_skills[skill.name] = injection
        ctx.agent.inject_system_message(injection)
        return (
            f"Skill '{skill_name}' loaded. "
            "Instructions injected into subsequent messages."
        )
