"""MCP client for connecting to external tool servers."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from typing import Any

from lukawi.tools.base import ToolDefinition, ToolResult, ToolParameter, ToolParameterType

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    command: list[str]
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)


_JSON_TYPE_MAP: dict[str, ToolParameterType] = {
    "string": ToolParameterType.STRING,
    "number": ToolParameterType.NUMBER,
    "integer": ToolParameterType.NUMBER,
    "boolean": ToolParameterType.BOOLEAN,
}


def _map_json_type(json_type: str) -> ToolParameterType:
    return _JSON_TYPE_MAP.get(json_type, ToolParameterType.STRING)


class MCPClient:
    """Client for connecting to MCP servers via stdio."""
    
    def __init__(self, config: MCPServerConfig):
        """Initialize MCP client.
        
        Args:
            config: Server configuration
        """
        self.config = config
        self._process: asyncio.subprocess.Process | None = None
        self._request_id = 0
        self._stderr_task: asyncio.Task | None = None
    
    async def connect(self) -> None:
        """Connect to the MCP server."""
        if self._process is not None:
            return

        cmd = list(self.config.command) + list(self.config.args)

        if sys.platform == "win32" and cmd:
            cmd = ["cmd", "/c"] + cmd

        env = None
        if self.config.env:
            env = dict(os.environ)
            env.update(self.config.env)

        async def _connect_impl() -> None:
            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            self._stderr_task = asyncio.create_task(self._consume_stderr())

            response = await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "lukawi",
                    "version": "0.1.0"
                }
            })

            if not response:
                raise RuntimeError("MCP initialize failed: empty response from server")

        try:
            await asyncio.wait_for(_connect_impl(), timeout=60.0)
        except asyncio.TimeoutError:
            raise TimeoutError("MCP server connection timed out")
    
    async def _consume_stderr(self) -> None:
        try:
            async for line in self._process.stderr:
                logger.debug(f"[MCP stderr] {line.decode().rstrip()}")
        except Exception as e:
            logger.debug(f"[MCP stderr] error reading stderr: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if not self._process:
            return

        if self._stderr_task:
            self._stderr_task.cancel()
            self._stderr_task = None

        try:
            shutdown_msg = json.dumps({"jsonrpc": "2.0", "method": "shutdown", "params": {}}) + "\n"
            exit_msg = json.dumps({"jsonrpc": "2.0", "method": "exit", "params": {}}) + "\n"
            if self._process.stdin:
                self._process.stdin.write(shutdown_msg.encode())
                self._process.stdin.write(exit_msg.encode())
                await self._process.stdin.drain()
        except Exception as e:
            logger.debug(f"Error sending shutdown to MCP server: {e}")

        try:
            if self._process.stdin:
                self._process.stdin.close()
        except Exception as e:
            logger.debug(f"Error closing MCP server stdin: {e}")

        self._process.terminate()
        try:
            await asyncio.wait_for(self._process.wait(), timeout=5.0)
        except Exception as e:
            logger.warning(f"MCP disconnect error: {e}")
            try:
                self._process.kill()
            except Exception as e:
                logger.debug(f"Error killing MCP server process: {e}")
        self._process = None
    
    async def list_tools(self) -> list[ToolDefinition]:
        """List available tools from the server.
        
        Returns:
            List of tool definitions
        """
        response = await self._send_request("tools/list", {})
        
        tools = []
        for tool_data in response.get("tools", []):
            parameters = []
            for param_name, param_data in tool_data.get("inputSchema", {}).get("properties", {}).items():
                json_type = param_data.get("type", "string")
                parameters.append(ToolParameter(
                    name=param_name,
                    type=_map_json_type(json_type),
                    description=param_data.get("description", ""),
                    required=param_name in tool_data.get("inputSchema", {}).get("required", [])
                ))
            
            tools.append(ToolDefinition(
                name=tool_data["name"],
                description=tool_data.get("description", ""),
                parameters=parameters
            ))
        
        return tools
    
    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any]
    ) -> ToolResult:
        """Call a tool on the server.
        
        Args:
            name: Tool name
            arguments: Tool arguments
        
        Returns:
            ToolResult from execution
        """
        response = await self._send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })
        
        content = response.get("content", [])
        if content:
            text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
            return ToolResult.success(result="\n".join(text_parts))
        
        return ToolResult.success(result="")
    
    async def _send_request(
        self,
        method: str,
        params: dict[str, Any]
    ) -> dict[str, Any]:
        if not self._process or not self._process.stdin or not self._process.stdout:
            raise RuntimeError("Not connected to MCP server")

        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params
        }

        request_str = json.dumps(request) + "\n"
        try:
            self._process.stdin.write(request_str.encode())
            await self._process.stdin.drain()
            response_str = await asyncio.wait_for(
                self._process.stdout.readline(), timeout=30.0
            )
        except asyncio.TimeoutError:
            raise RuntimeError(f"MCP request timed out after 30s: {method}")
        except BrokenPipeError:
            raise RuntimeError(f"MCP server disconnected: {method}")
        except Exception as e:
            raise RuntimeError(f"MCP request failed: {method} - {e}")

        response = json.loads(response_str)
        if "error" in response:
            raise RuntimeError(f"MCP error: {response['error']}")
        return response.get("result", {})
