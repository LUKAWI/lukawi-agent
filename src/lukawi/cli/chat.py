from __future__ import annotations

import asyncio
import sys

from lukawi.agent.core import AgentEventType
from lukawi.cli import create_agent_context, cleanup_context


def run_chat(
    text: str,
    config_path: str | None = None,
    model: str | None = None,
    debug: bool = False,
    mock: bool = False,
    mcp_path: str | None = None,
    skills_dir: str | None = None,
) -> None:
    ctx = create_agent_context(config_path, model, debug, mock, mcp_path, skills_dir)

    async def _run() -> None:
        async for event in ctx.agent.run(text):
            if event.type == AgentEventType.FINAL_ANSWER:
                print(event.data["content"], end="", flush=True)
                print()
            elif event.type == AgentEventType.ERROR:
                print(event.data["error"], file=sys.stderr)

    try:
        asyncio.run(_run())
    finally:
        cleanup_context(ctx)
