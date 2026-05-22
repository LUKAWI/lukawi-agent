from __future__ import annotations

from lukawi.cli import cleanup_context, create_agent_context
from rich import print as rich_print
from rich.table import Table


def run_status(
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
        table = Table(title="System Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")

        model_name = ctx.model_registry.current_name if ctx.model_registry else "none"
        table.add_row("Model", model_name or "none")

        tool_count = ctx.tool_registry.count
        table.add_row("Tools", str(tool_count))

        mcp_count = ctx.mcp_manager.connected_count
        table.add_row("MCP", str(mcp_count))

        memory_status = "enabled" if ctx.memory_manager else "disabled"
        table.add_row("Memory", memory_status)

        skill_count = len(ctx.skill_loader.list_skills()) if ctx.skill_loader else 0
        table.add_row("Skills", str(skill_count))

        rich_print(table)
    finally:
        cleanup_context(ctx)
