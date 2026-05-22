from __future__ import annotations

from lukawi.cli import cleanup_context, create_agent_context
from rich import print as rich_print


def run_skills(
    config_path: str | None = None,
    model: str | None = None,
    debug: bool = False,
    mock: bool = False,
    mcp_path: str | None = None,
    skills_dir: str | None = None,
) -> None:
    ctx = create_agent_context(
        config_path=config_path,
        model=model,
        debug=debug,
        mock=mock,
        mcp_path=mcp_path,
        skills_dir=skills_dir,
    )
    try:
        skills = ctx.skill_loader.list_skills() if ctx.skill_loader else []
        if skills:
            for skill in skills:
                rich_print(f"  [cyan]{skill.name}[/cyan]: {skill.description}")
        else:
            rich_print("  No skills loaded")
    finally:
        cleanup_context(ctx)
