"""Agent tool gateway with policy enforcement."""

from __future__ import annotations

from typing import Any

from lukawi.tools.base import ToolDefinition, ToolResult
from lukawi.tools.registry import ToolRegistry, ToolNotFoundError
from lukawi.tools.policy import ToolPolicy, PolicyContext
from lukawi.tools.executor import ToolExecutor


class ToolGateway:
    """Gateway for executing tools with policy enforcement."""

    def __init__(
        self,
        registry: ToolRegistry,
        policy: ToolPolicy | None = None,
        executor: ToolExecutor | None = None,
    ):
        self.registry = registry
        self.policy = policy
        self.executor = executor or ToolExecutor()

        self.call_count = 0
        self.denied_count = 0

    async def execute(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        context: PolicyContext | None = None,
    ) -> ToolResult:
        self.call_count += 1

        if self.policy and context:
            if not self.policy.is_allowed(tool_name, context):
                self.denied_count += 1
                return ToolResult.denied(
                    f"Tool '{tool_name}' denied by policy"
                )

        try:
            definition, handler = self.registry.get(tool_name)
        except ToolNotFoundError:
            return ToolResult.error(f"Tool '{tool_name}' not found")

        return await self.executor.execute(
            definition=definition,
            handler=handler,
            parameters=parameters,
        )

    def get_available_tools(
        self,
        context: PolicyContext | None = None,
    ) -> list[ToolDefinition]:
        tools = self.registry.list_tools()

        if self.policy and context:
            return self.policy.filter_tools(tools, context)

        return tools

    def reset_stats(self) -> None:
        self.call_count = 0
        self.denied_count = 0
