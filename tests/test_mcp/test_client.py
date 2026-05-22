"""Tests for MCP client."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from lukawi.mcp.client import (
    MCPClient,
    MCPServerConfig,
    _map_json_type,
    _JSON_TYPE_MAP,
)
from lukawi.tools.base import ToolParameterType


class TestMapJsonType:
    """Tests for the _map_json_type mapping function."""

    def test_maps_string(self):
        assert _map_json_type("string") == ToolParameterType.STRING

    def test_maps_number(self):
        assert _map_json_type("number") == ToolParameterType.NUMBER

    def test_maps_integer(self):
        assert _map_json_type("integer") == ToolParameterType.NUMBER

    def test_maps_boolean(self):
        assert _map_json_type("boolean") == ToolParameterType.BOOLEAN

    def test_defaults_to_string_for_unknown(self):
        assert _map_json_type("array") == ToolParameterType.STRING
        assert _map_json_type("object") == ToolParameterType.STRING
        assert _map_json_type("null") == ToolParameterType.STRING
        assert _map_json_type("") == ToolParameterType.STRING

    def test_map_contains_expected_keys(self):
        assert set(_JSON_TYPE_MAP.keys()) == {"string", "number", "integer", "boolean"}


class TestMCPClientConnect:
    """Tests for MCPClient.connect()."""

    @pytest.fixture
    def config(self):
        return MCPServerConfig(name="test", command=["echo", "hello"])

    @pytest.fixture
    def mock_process(self):
        proc = AsyncMock()
        proc.stdin = AsyncMock()
        proc.stdout = AsyncMock()
        proc.stderr = AsyncMock()
        proc.returncode = None
        return proc

    async def test_connect_reentry_protection(self, config, mock_process):
        client = MCPClient(config)
        client._process = mock_process
        original_process = client._process

        with patch.object(client, '_send_request') as mock_send:
            await client.connect()

        mock_send.assert_not_called()
        assert client._process is original_process

    async def test_connect_creates_process_when_none(self, config):
        client = MCPClient(config)

        with (
            patch("lukawi.mcp.client.asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_create,
            patch.object(client, '_send_request', new_callable=AsyncMock) as mock_send,
        ):
            mock_proc = AsyncMock()
            mock_proc.stdin = MagicMock()
            mock_proc.stdout = MagicMock()
            mock_create.return_value = mock_proc
            mock_send.return_value = {"protocolVersion": "2024-11-05"}

            await client.connect()

            mock_create.assert_awaited_once()
            mock_send.assert_awaited_once_with("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "lukawi", "version": "0.1.0"}
            })

    async def test_connect_with_env(self, config):
        config_with_env = MCPServerConfig(
            name="test", command=["echo"], env={"MY_VAR": "my_value"}
        )
        client = MCPClient(config_with_env)

        with (
            patch("lukawi.mcp.client.asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_create,
            patch.object(client, '_send_request', new_callable=AsyncMock) as mock_send,
        ):
            mock_proc = AsyncMock()
            mock_proc.stdin = MagicMock()
            mock_proc.stdout = MagicMock()
            mock_create.return_value = mock_proc
            mock_send.return_value = {"protocolVersion": "2024-11-05"}

            with patch("lukawi.mcp.client.os.environ", {"PATH": "/usr/bin"}):
                await client.connect()

            _call_env = mock_create.call_args[1].get("env")
            assert _call_env is not None
            assert _call_env["MY_VAR"] == "my_value"
            assert _call_env["PATH"] == "/usr/bin"

    async def test_connect_without_env_passes_none(self, config):
        client = MCPClient(config)

        with (
            patch("lukawi.mcp.client.asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_create,
            patch.object(client, '_send_request', new_callable=AsyncMock) as mock_send,
        ):
            mock_proc = AsyncMock()
            mock_proc.stdin = MagicMock()
            mock_proc.stdout = MagicMock()
            mock_create.return_value = mock_proc
            mock_send.return_value = {"protocolVersion": "2024-11-05"}

            await client.connect()

            assert mock_create.call_args[1].get("env") is None

    async def test_connect_raises_on_empty_initialize_response(self, config):
        client = MCPClient(config)

        with (
            patch("lukawi.mcp.client.asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_create,
            patch.object(client, '_send_request', new_callable=AsyncMock) as mock_send,
        ):
            mock_proc = AsyncMock()
            mock_proc.stdin = MagicMock()
            mock_proc.stdout = MagicMock()
            mock_create.return_value = mock_proc
            mock_send.return_value = {}

            with pytest.raises(RuntimeError, match="empty response"):
                await client.connect()


class TestMCPClientDisconnect:
    """Tests for MCPClient.disconnect()."""

    @pytest.fixture
    def config(self):
        return MCPServerConfig(name="test", command=["echo"])

    @pytest.fixture
    def client_with_process(self, config):
        client = MCPClient(config)
        proc = AsyncMock(spec=asyncio.subprocess.Process)
        proc.stdin = MagicMock()
        proc.stdin.drain = AsyncMock()
        proc.stdout = MagicMock()
        proc.stderr = MagicMock()
        proc.returncode = None
        client._process = proc
        return client

    async def test_disconnect_sends_notifications(self, client_with_process):
        client = client_with_process
        stdin = client._process.stdin
        await client.disconnect()

        assert stdin.write.call_count >= 2
        write_calls = [c.args[0] for c in stdin.write.call_args_list]
        all_written = b"".join(write_calls)
        assert b'"shutdown"' in all_written
        assert b'"exit"' in all_written
        stdin.drain.assert_awaited()

    async def test_disconnect_closes_stdin(self, client_with_process):
        client = client_with_process
        stdin = client._process.stdin
        await client.disconnect()

        stdin.close.assert_called_once()

    async def test_disconnect_calls_terminate_and_wait(self, client_with_process):
        client = client_with_process
        proc = client._process
        await client.disconnect()

        proc.terminate.assert_called_once()
        proc.wait.assert_awaited_once()

    async def test_disconnect_sets_process_to_none(self, client_with_process):
        client = client_with_process
        await client.disconnect()

        assert client._process is None

    async def test_disconnect_noop_when_no_process(self, config):
        client = MCPClient(config)
        await client.disconnect()
        assert client._process is None

    async def test_disconnect_handles_exception_gracefully(self, client_with_process):
        client = client_with_process
        client._process.wait = AsyncMock(side_effect=RuntimeError("wait failed"))

        await client.disconnect()

        assert client._process is None

    async def test_disconnect_logs_warning_on_timeout(self, client_with_process):
        client = client_with_process
        client._process.wait = AsyncMock(side_effect=asyncio.TimeoutError("timed out"))

        with patch("lukawi.mcp.client.logger") as mock_logger:
            await client.disconnect()

            mock_logger.warning.assert_called_once()
            assert "timeout" in str(mock_logger.warning.call_args).lower() or \
                   "timed out" in str(mock_logger.warning.call_args).lower() or \
                   "disconnect" in str(mock_logger.warning.call_args).lower()


class TestMCPClientListTools:
    """Tests for MCPClient.list_tools()."""

    @pytest.fixture
    def config(self):
        return MCPServerConfig(name="test", command=["echo"])

    @pytest.fixture
    def client(self, config):
        return MCPClient(config)

    async def test_list_tools_maps_parameter_types(self, client):
        response = {
            "tools": [
                {
                    "name": "test_tool",
                    "description": "A test tool",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Name input"},
                            "count": {"type": "integer", "description": "Count input"},
                            "price": {"type": "number", "description": "Price input"},
                            "active": {"type": "boolean", "description": "Active flag"},
                            "tags": {"type": "array", "description": "Tags list"},
                        },
                        "required": ["name", "count"]
                    }
                }
            ]
        }

        with patch.object(client, '_send_request', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = response
            tools = await client.list_tools()

        assert len(tools) == 1
        tool = tools[0]
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"

        params = {p.name: p for p in tool.parameters}
        assert params["name"].type == ToolParameterType.STRING
        assert params["name"].required is True
        assert params["count"].type == ToolParameterType.NUMBER
        assert params["count"].required is True
        assert params["price"].type == ToolParameterType.NUMBER
        assert params["price"].required is False
        assert params["active"].type == ToolParameterType.BOOLEAN
        assert params["tags"].type == ToolParameterType.STRING  # unknown -> default

    async def test_list_tools_empty_response(self, client):
        with patch.object(client, '_send_request', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {}
            tools = await client.list_tools()

        assert tools == []

    async def test_list_tools_no_tools_key(self, client):
        with patch.object(client, '_send_request', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"other": "data"}
            tools = await client.list_tools()

        assert tools == []


class TestMCPClientCallTool:
    """Tests for MCPClient.call_tool()."""

    @pytest.fixture
    def config(self):
        return MCPServerConfig(name="test", command=["echo"])

    @pytest.fixture
    def client(self, config):
        return MCPClient(config)

    async def test_call_tool_returns_text_content(self, client):
        response = {
            "content": [
                {"type": "text", "text": "Hello"},
                {"type": "text", "text": "World"},
            ]
        }

        with patch.object(client, '_send_request', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = response
            result = await client.call_tool("echo", {"msg": "hi"})

        assert result.status.value == "success"
        assert result.result == "Hello\nWorld"

    async def test_call_tool_empty_content(self, client):
        with patch.object(client, '_send_request', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"content": []}
            result = await client.call_tool("echo", {})

        assert result.status.value == "success"
        assert result.result == ""

    async def test_call_tool_no_content_key(self, client):
        with patch.object(client, '_send_request', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {}
            result = await client.call_tool("echo", {})

        assert result.status.value == "success"
        assert result.result == ""


class TestMCPClientSendRequest:
    """Tests for MCPClient._send_request()."""

    @pytest.fixture
    def config(self):
        return MCPServerConfig(name="test", command=["echo"])

    @pytest.fixture
    def client(self, config):
        return MCPClient(config)

    def test_send_request_raises_when_not_connected(self, client):
        with pytest.raises(RuntimeError, match="Not connected"):
            asyncio.run(client._send_request("test", {}))
