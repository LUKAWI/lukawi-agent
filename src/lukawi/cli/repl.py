from __future__ import annotations

import asyncio
import sys
import signal

from lukawi.cli import create_agent_context, cleanup_context
from lukawi.agent.core import AgentEventType
from rich import print as rprint
from rich.prompt import Prompt


def run_repl(
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
        rprint("[bold green]Lukawi Agent v0.1.0[/bold green]")
        rprint("Type /help for commands, /quit to exit.")

        async def _handle_message(text: str) -> None:
            async for event in ctx.agent.run(text):
                if event.type == AgentEventType.FINAL_ANSWER:
                    rprint(event.data.get("content", ""))
                elif event.type == AgentEventType.TOOL_CALL:
                    tool = event.data.get("tool", "unknown")
                    rprint(f"[dim]\U0001f527 Using {tool}...[/dim]")
                elif event.type == AgentEventType.TOOL_RESULT:
                    result = event.data.get("result")
                    tool = event.data.get("tool", "unknown")
                    if result and hasattr(result, "status") and result.status.value == "error":
                        rprint(f"[red]\U0001f527 Tool {tool} error: {result.error_message}[/red]")
                elif event.type == AgentEventType.ERROR:
                    error = event.data.get("error", "Unknown error")
                    rprint(f"[red]Error: {error}[/red]")

        async def _repl_loop() -> None:
            while True:
                try:
                    text = Prompt.ask("[bold cyan]>>>[/bold cyan]")
                except (KeyboardInterrupt, EOFError):
                    rprint("\nBye!")
                    break

                if not text:
                    continue

                if text.startswith("/"):
                    cmd = text.lower().strip()
                    if cmd in ("/quit", "/exit"):
                        rprint("Bye!")
                        break
                    elif cmd == "/help":
                        rprint("[bold]Available commands:[/bold]")
                        rprint("  /help        - Show this help message")
                        rprint("  /quit, /exit - Exit the REPL")
                        rprint("  /models      - List available models")
                        rprint("  /status      - Show agent status")
                        rprint("  /clear       - Clear conversation memory")
                    elif cmd == "/models":
                        if ctx.model_registry:
                            models = ctx.model_registry.list_registered()
                            if models:
                                rprint("[bold]Available models:[/bold]")
                                for name, info in models:
                                    current = " (current)" if name == ctx.model_registry.current_name else ""
                                    rprint(f"  {name}{current}")
                            else:
                                rprint("No models registered.")
                        else:
                            rprint("[yellow]No model registry available.[/yellow]")
                    elif cmd == "/status":
                        rprint("[bold]Agent Status:[/bold]")
                        rprint(f"  Model: {ctx.model_registry.current_name if ctx.model_registry else 'N/A'}")
                        rprint(f"  Tools: {len(ctx.tool_registry.list_tools())} registered")
                        if ctx.mcp_manager:
                            rprint(f"  MCP: {ctx.mcp_manager.connected_count} connected")
                        if ctx.memory_manager:
                            rprint("  Memory: enabled")
                        else:
                            rprint("  Memory: disabled")
                    elif cmd == "/clear":
                        if ctx.memory_manager:
                            ctx.memory_manager.clear_session()
                            rprint("[green]Conversation memory cleared.[/green]")
                        else:
                            rprint("[yellow]No memory manager available.[/yellow]")
                    else:
                        rprint(f"[red]Unknown command: {cmd}[/red]")
                else:
                    await _handle_message(text)

        try:
            asyncio.run(_repl_loop())
        except KeyboardInterrupt:
            rprint("\nBye!")

    finally:
        cleanup_context(ctx)
