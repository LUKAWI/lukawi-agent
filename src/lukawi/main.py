"""Main entry point for Lukawi Agent."""

from __future__ import annotations

import argparse

from lukawi import __version__
from lukawi.cli.chat import run_chat
from lukawi.cli.config import run_config
from lukawi.cli.models import run_models
from lukawi.cli.repl import run_repl
from lukawi.cli.skills import run_skills
from lukawi.cli.status import run_status
from lukawi.cli.webui import run_webui
from lukawi.tui.app import run_tui


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lukawi Agent - AI Assistant with Tools"
    )
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    parser.add_argument("--model", type=str, default=None, help="Model to use (overrides config)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--mock", action="store_true", help="Use mock LLM provider")
    parser.add_argument("--mcp", type=str, default=None, help="Path to MCP config file")
    parser.add_argument("--skills-dir", type=str, default=None, help="Directory containing skills")
    parser.add_argument("--version", action="store_true", help="Show version")

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("tui", help="Launch terminal UI")
    subparsers.add_parser("webui", help="Launch web UI")

    chat_parser = subparsers.add_parser("chat", help="One-shot chat message")
    chat_parser.add_argument("text", type=str, help="Message text")

    subparsers.add_parser("models", help="List and switch models")
    subparsers.add_parser("config", help="View and edit configuration")
    subparsers.add_parser("skills", help="Manage skills")
    subparsers.add_parser("status", help="Show agent status")

    return parser.parse_args(argv)


def _shared_kwargs(args: argparse.Namespace) -> dict:
    return {
        "config_path": args.config,
        "model": args.model,
        "debug": args.debug,
        "mock": args.mock,
        "mcp_path": args.mcp,
        "skills_dir": args.skills_dir,
    }


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    if args.version:
        print(f"lukawi {__version__}")
        return

    kwargs = _shared_kwargs(args)

    if args.command == "tui":
        run_tui(**kwargs)
    elif args.command == "webui":
        run_webui(**kwargs)
    elif args.command == "chat":
        run_chat(args.text, **kwargs)
    elif args.command == "models":
        run_models(**kwargs)
    elif args.command == "config":
        run_config(**kwargs)
    elif args.command == "skills":
        run_skills(**kwargs)
    elif args.command == "status":
        run_status(**kwargs)
    else:
        run_repl(**kwargs)


if __name__ == "__main__":
    main()
