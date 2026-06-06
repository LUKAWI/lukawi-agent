"""User-level config directory (~/.lukawi/) for persistent MCP server configs."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from lukawi.mcp.client import MCPServerConfig


def get_user_dir() -> Path:
    """Get the ~/.lukawi user config directory, creating it if needed."""
    path = Path.home() / ".lukawi"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_mcp_servers_file() -> Path:
    return get_user_dir() / "mcp-servers.json"


def save_mcp_servers(servers: list[MCPServerConfig]) -> None:
    """Save MCP server configurations to ~/.lukawi/mcp-servers.json.

    Args:
        servers: List of server configurations to persist
    """
    data = [
        {
            "name": s.name,
            "command": list(s.command) if s.command else [],
            "args": list(s.args) if s.args else [],
            "env": dict(s.env) if s.env else {},
        }
        for s in servers
    ]
    path = get_mcp_servers_file()
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_mcp_servers() -> list[MCPServerConfig]:
    """Load saved MCP server configurations from ~/.lukawi/mcp-servers.json.

    Returns:
        List of saved server configs, empty list if file doesn't exist
    """
    path = get_mcp_servers_file()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [
            MCPServerConfig(
                name=item.get("name", "unknown"),
                command=item.get("command", []),
                args=item.get("args", []),
                env=item.get("env", {}),
            )
            for item in data
        ]
    except (json.JSONDecodeError, OSError) as e:
        logging.warning(f"Failed to load MCP servers from {path}: {e}")
        return []


def merge_mcp_configs(
    project_servers: list[MCPServerConfig],
    user_servers: list[MCPServerConfig],
) -> list[MCPServerConfig]:
    """Merge project-level and user-level MCP configs.

    User servers override project servers with the same name.
    Project servers not overridden are kept.

    Args:
        project_servers: Servers from project config/default.yaml
        user_servers: Servers from ~/.lukawi/mcp-servers.json

    Returns:
        Merged list of server configs
    """
    by_name: dict[str, MCPServerConfig] = {}
    for s in project_servers:
        by_name[s.name] = s
    for s in user_servers:
        by_name[s.name] = s
    return list(by_name.values())
