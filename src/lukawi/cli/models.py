from __future__ import annotations

from lukawi.cli import cleanup_context, create_agent_context
from rich import print as rich_print


def run_models(
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
        rich_print("[bold]Available Models:[/bold]")
        if ctx.model_registry:
            current = ctx.model_registry.current_name
            for name, info in ctx.model_registry.list_registered():
                marker = " [green]*[/green]" if name == current else "  "
                rich_print(f"  {marker} {name} ({info.provider})")
        else:
            rich_print("  No models configured")
    finally:
        cleanup_context(ctx)
