from __future__ import annotations

import os
import webbrowser

import uvicorn

from lukawi.cli import create_agent_context, cleanup_context
from lukawi.server.app import create_app
from lukawi.server.state import ServerState


def run_webui(
    config_path: str | None = None,
    model: str | None = None,
    debug: bool = False,
    mock: bool = False,
    mcp_path: str | None = None,
    skills_dir: str | None = None,
) -> None:
    ctx = create_agent_context(config_path, model, debug, mock, mcp_path, skills_dir)

    try:
        server_state = ServerState(
            agent=ctx.agent,
            model_registry=ctx.model_registry,
            tool_registry=ctx.tool_registry,
            mcp_manager=ctx.mcp_manager,
            mcp_configs=ctx.mcp_configs,
            config=ctx.config,
            tui_config=ctx.config.tui,
            memory_manager=ctx.memory_manager,
            rag_manager=ctx.rag_manager,
        )

        app = create_app(server_state)

        port = int(os.environ.get("LUKAWI_PORT", "8000"))
        webbrowser.open(f"http://localhost:{port}")

        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    finally:
        cleanup_context(ctx)
