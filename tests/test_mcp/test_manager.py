"""Tests for MCP manager - disconnect and tool registry cleanup."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from lukawi.mcp.manager import MCPManager
from lukawi.mcp.client import MCPServerConfig
from lukawi.tools.registry import ToolRegistry
from lukawi.tools.base import ToolDefinition, ToolResult, ToolParameter, ToolParameterType


@pytest.fixture
def registry():
    return ToolRegistry()


@pytest.fixture
def manager():
    return MCPManager()


@pytest.fixture
def mock_tool_def():
    return ToolDefinition(
        name="mcp_test_tool",
        description="MCP test tool",
        parameters=[
            ToolParameter(
                name="input",
                type=ToolParameterType.STRING,
                description="Input value"
            )
        ]
    )


@pytest.fixture
def mock_handler():
    async def handler(**params) -> ToolResult:
        return ToolResult.success("ok")
    return handler


class TestMCPManagerDisconnect:
    """Tests for MCPManager disconnect and tool registry cleanup."""

    async def test_disconnect_server_cleans_up_tools(self, manager, registry, mock_tool_def, mock_handler):
        registry.register(mock_tool_def, mock_handler)
        assert registry.has("mcp_test_tool")

        manager._tool_registry = registry
        manager._server_tools["test_server"] = ["mcp_test_tool"]

        mock_client = AsyncMock()
        manager._clients["test_server"] = mock_client

        await manager.disconnect_server("test_server")

        assert not registry.has("mcp_test_tool")
        assert "test_server" not in manager._server_tools
        assert "test_server" not in manager._clients
        mock_client.disconnect.assert_awaited_once()

    async def test_disconnect_server_no_registry(self, manager):
        mock_client = AsyncMock()
        manager._clients["test_server"] = mock_client

        result = await manager.disconnect_server("test_server")

        assert result is True
        assert "test_server" not in manager._clients
        mock_client.disconnect.assert_awaited_once()

    async def test_disconnect_server_not_found(self, manager):
        result = await manager.disconnect_server("nonexistent")

        assert result is False

    async def test_disconnect_server_multiple_tools(self, manager, registry):
        tools = []
        for i in range(3):
            tool = ToolDefinition(
                name=f"mcp_tool_{i}",
                description=f"MCP tool {i}",
                parameters=[]
            )
            registry.register(tool, AsyncMock())
            tools.append(tool)

        assert registry.count == 3

        manager._tool_registry = registry
        manager._server_tools["server_a"] = ["mcp_tool_0", "mcp_tool_1"]
        manager._server_tools["server_b"] = ["mcp_tool_2"]

        mock_client_a = AsyncMock()
        mock_client_b = AsyncMock()
        manager._clients["server_a"] = mock_client_a
        manager._clients["server_b"] = mock_client_b

        await manager.disconnect_server("server_a")

        assert not registry.has("mcp_tool_0")
        assert not registry.has("mcp_tool_1")
        assert registry.has("mcp_tool_2")
        assert registry.count == 1
        assert "server_a" not in manager._server_tools
        assert "server_a" not in manager._clients
        assert "server_b" in manager._server_tools
        assert "server_b" in manager._clients

        mock_client_a.disconnect.assert_awaited_once()
        mock_client_b.disconnect.assert_not_awaited()

    async def test_disconnect_all_cleans_up_all_tools(self, manager, registry):
        tool_names = []
        for i in range(3):
            name = f"mcp_tool_{i}"
            tool = ToolDefinition(
                name=name,
                description=f"MCP tool {i}",
                parameters=[]
            )
            registry.register(tool, AsyncMock())
            tool_names.append(name)

        assert registry.count == 3

        manager._tool_registry = registry
        manager._server_tools["server_a"] = ["mcp_tool_0"]
        manager._server_tools["server_b"] = ["mcp_tool_1", "mcp_tool_2"]

        mock_client_a = AsyncMock()
        mock_client_b = AsyncMock()
        manager._clients["server_a"] = mock_client_a
        manager._clients["server_b"] = mock_client_b

        await manager.disconnect_all()

        assert registry.count == 0
        assert len(manager._server_tools) == 0
        assert len(manager._clients) == 0
        mock_client_a.disconnect.assert_awaited_once()
        mock_client_b.disconnect.assert_awaited_once()

    async def test_disconnect_all_no_tools_registered(self, manager):
        mock_client = AsyncMock()
        manager._clients["test_server"] = mock_client

        await manager.disconnect_all()

        assert len(manager._clients) == 0
        mock_client.disconnect.assert_awaited_once()

    async def test_disconnect_all_partial_registry(self, manager, registry):
        tool = ToolDefinition(name="only_tool", description="Only tool", parameters=[])
        registry.register(tool, AsyncMock())

        manager._tool_registry = registry
        manager._server_tools["server_a"] = ["only_tool"]
        manager._server_tools["server_b"] = []

        mock_client_a = AsyncMock()
        mock_client_b = AsyncMock()
        manager._clients["server_a"] = mock_client_a
        manager._clients["server_b"] = mock_client_b

        await manager.disconnect_all()

        assert registry.count == 0
        assert len(manager._server_tools) == 0
        assert len(manager._clients) == 0
