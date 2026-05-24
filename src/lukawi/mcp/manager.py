"""MCP connection manager - connects servers and registers their tools."""

from __future__ import annotations

import asyncio
import logging

from lukawi.mcp.client import MCPClient, MCPServerConfig
from lukawi.tools.registry import ToolRegistry
from lukawi.tools.base import ToolResult

logger = logging.getLogger(__name__)


def _make_mcp_handler(client: MCPClient, tool_name: str):
    """Create a handler function that routes tool calls to an MCP client."""
    async def handler(**params) -> ToolResult:
        return await client.call_tool(tool_name, params)
    return handler


class MCPManager:
    """Manages multiple MCP server connections.

    Usage:
        manager = MCPManager()

        # Connect all servers and register tools
        await manager.connect_all(configs)
        await manager.register_tools(tool_registry)

        # On shutdown
        await manager.disconnect_all()
    """

    def __init__(self):
        self._clients: dict[str, MCPClient] = {}
        self._tool_registry: ToolRegistry | None = None
        self._server_tools: dict[str, list[str]] = {}

    async def connect_all(self, configs: list[MCPServerConfig]) -> None:
        """Connect to all configured MCP servers.

        Args:
            configs: List of server configurations
        """
        async def _connect_one(cfg: MCPServerConfig) -> None:
            client = MCPClient(cfg)
            await client.connect()
            self._clients[cfg.name] = client

        tasks = [_connect_one(cfg) for cfg in configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for cfg, result in zip(configs, results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to connect MCP server '{cfg.name}': {result}")

    async def register_tools(self, registry: ToolRegistry) -> None:
        """Discover tools from all connected servers and register them.

        Each MCP tool gets registered as a standalone ToolDefinition
        with a handler that routes through its MCP client.

        Args:
            registry: ToolRegistry to register tools into
        """
        self._tool_registry = registry
        for name, client in self._clients.items():
            try:
                tools = await client.list_tools()
                tool_names: list[str] = []
                for tool_def in tools:
                    handler = _make_mcp_handler(client, tool_def.name)
                    try:
                        registry.register(tool_def, handler)
                        tool_names.append(tool_def.name)
                    except Exception as e:
                        logger.warning(f"Failed to register tool '{tool_def.name}' from '{name}': {e}")
                self._server_tools[name] = tool_names
            except Exception as e:
                logger.warning(f"Failed to list tools from '{name}': {e}")

    async def connect_server(self, config: MCPServerConfig, registry: ToolRegistry | None = None) -> bool:
        """Connect a single MCP server and optionally register its tools.

        Args:
            config: Server configuration
            registry: If provided, discovered tools are registered here

        Returns:
            True if connected successfully
        """
        client = MCPClient(config)
        try:
            await client.connect()
            self._clients[config.name] = client
            if registry:
                self._tool_registry = registry
                tools = await client.list_tools()
                tool_names: list[str] = []
                for tool_def in tools:
                    handler = _make_mcp_handler(client, tool_def.name)
                    try:
                        registry.register(tool_def, handler)
                        tool_names.append(tool_def.name)
                    except Exception as e:
                        logger.warning(f"Failed to register tool '{tool_def.name}' from '{config.name}': {e}")
                self._server_tools[config.name] = tool_names
            return True
        except Exception as e:
            logger.warning(f"Failed to connect MCP server '{config.name}': {e}")
            return False

    def _unregister_server_tools(self, name: str) -> None:
        """Unregister all tools belonging to a server from the registry."""
        if self._tool_registry is not None and name in self._server_tools:
            for tool_name in self._server_tools[name]:
                try:
                    self._tool_registry.unregister(tool_name)
                except Exception as e:
                    logger.warning(f"Failed to unregister tool '{tool_name}' from '{name}': {e}")
            del self._server_tools[name]

    async def disconnect_server(self, name: str) -> bool:
        """Disconnect a single MCP server.

        Args:
            name: Server name to disconnect

        Returns:
            True if disconnected
        """
        self._unregister_server_tools(name)
        client = self._clients.pop(name, None)
        if client:
            try:
                await client.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting MCP server '{name}': {e}")
            return True
        return False

    async def disconnect_all(self) -> None:
        for name in list(self._server_tools.keys()):
            self._unregister_server_tools(name)
        for name, client in self._clients.items():
            try:
                await client.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting MCP server '{name}': {e}")
        self._clients.clear()

    @property
    def connected_count(self) -> int:
        return len(self._clients)

    @property
    def connected_servers(self) -> list[str]:
        return list(self._clients.keys())
