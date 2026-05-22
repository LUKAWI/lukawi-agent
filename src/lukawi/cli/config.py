from __future__ import annotations

import json

from lukawi.cli import cleanup_context, create_agent_context


def run_config(
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
        print(f"Config Path: {config_path or 'default'}")
        summary = {
            "model.default": ctx.config.model.default,
            "memory.enabled": ctx.config.memory.enabled,
            "logging.level": ctx.config.logging.level,
            "skills.auto_load": ctx.config.skills.auto_load,
        }
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    finally:
        cleanup_context(ctx)
