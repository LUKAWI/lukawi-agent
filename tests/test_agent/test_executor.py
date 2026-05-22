"""Tests for agent tool gateway."""

import pytest

from lukawi.agent.executor import ToolGateway
from lukawi.tools.base import ToolDefinition, ToolParameter, ToolParameterType, ToolResult, ToolResultStatus
from lukawi.tools.registry import ToolRegistry
from lukawi.tools.policy import ToolPolicy, PolicyContext
from lukawi.config.models import ToolPolicyConfig, ToolProfileConfig


@pytest.fixture
def registry():
    reg = ToolRegistry()

    async def echo_handler(text: str) -> ToolResult:
        return ToolResult.success(f"Echo: {text}")

    reg.register(
        ToolDefinition(name="echo", description="Echo tool", parameters=[
            ToolParameter(name="text", type=ToolParameterType.STRING, description="Text to echo", required=True),
        ]),
        echo_handler
    )

    return reg


@pytest.fixture
def policy():
    config = ToolPolicyConfig(
        profiles={
            "default": ToolProfileConfig(allowed_tools=["*"]),
            "restricted": ToolProfileConfig(allowed_tools=["web_fetch"])
        }
    )
    return ToolPolicy(config)


@pytest.fixture
def gateway(registry, policy):
    return ToolGateway(registry=registry, policy=policy)


class TestToolGateway:
    @pytest.mark.asyncio
    async def test_execute_success(self, gateway):
        result = await gateway.execute(
            "echo",
            {"text": "hello"},
            PolicyContext(profile="default")
        )

        assert result.status == ToolResultStatus.SUCCESS
        assert result.result == "Echo: hello"
        assert gateway.call_count == 1

    @pytest.mark.asyncio
    async def test_execute_denied_by_policy(self, gateway):
        result = await gateway.execute(
            "echo",
            {"text": "hello"},
            PolicyContext(profile="restricted")
        )

        assert result.status == ToolResultStatus.DENIED
        assert gateway.denied_count == 1

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, gateway):
        result = await gateway.execute(
            "nonexistent",
            {},
            PolicyContext(profile="default")
        )

        assert result.status == ToolResultStatus.ERROR
        assert "not found" in result.error_message.lower()

    def test_get_available_tools(self, gateway):
        # Default profile allows all
        tools = gateway.get_available_tools(PolicyContext(profile="default"))
        assert len(tools) == 1

        # Restricted profile only allows web_fetch
        tools = gateway.get_available_tools(PolicyContext(profile="restricted"))
        assert len(tools) == 0  # echo is not in restricted profile

    def test_reset_stats(self, gateway):
        gateway.call_count = 5
        gateway.denied_count = 2

        gateway.reset_stats()

        assert gateway.call_count == 0
        assert gateway.denied_count == 0
