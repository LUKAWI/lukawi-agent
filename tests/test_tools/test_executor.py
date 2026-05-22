"""Tests for tool executor with hook system."""

import pytest
import asyncio

from lukawi.tools.executor import ToolExecutor, ToolHooks, HookDecision
from lukawi.tools.base import (
    ToolDefinition,
    ToolResult,
    ToolResultStatus,
    ToolParameter,
    ToolParameterType,
)


@pytest.fixture
def tool_def():
    return ToolDefinition(
        name="test_tool",
        description="Test tool",
        parameters=[
            ToolParameter(
                name="input",
                type=ToolParameterType.STRING,
                description="Input",
            )
        ],
    )


@pytest.fixture
def success_handler():
    async def handler(input: str) -> ToolResult:
        return ToolResult.success(f"Result: {input}")

    return handler


@pytest.fixture
def slow_handler():
    async def handler(input: str) -> ToolResult:
        await asyncio.sleep(10)
        return ToolResult.success("done")

    return handler


@pytest.fixture
def error_handler():
    async def handler(input: str) -> ToolResult:
        raise ValueError("Test error")

    return handler


@pytest.fixture
def executor():
    return ToolExecutor()


class TestToolExecutor:
    @pytest.mark.asyncio
    async def test_execute_success(self, executor, tool_def, success_handler):
        result = await executor.execute(
            tool_def, success_handler, {"input": "test"}
        )

        assert result.status == ToolResultStatus.SUCCESS
        assert result.result == "Result: test"

    @pytest.mark.asyncio
    async def test_execute_timeout(self, executor, tool_def, slow_handler):
        result = await executor.execute(
            tool_def, slow_handler, {"input": "test"}, timeout=0.1
        )

        assert result.status == ToolResultStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_execute_error(self, executor, tool_def, error_handler):
        result = await executor.execute(
            tool_def, error_handler, {"input": "test"}
        )

        assert result.status == ToolResultStatus.ERROR
        assert "Test error" in result.error_message

    @pytest.mark.asyncio
    async def test_pre_hook_can_deny(self, tool_def, success_handler):
        async def deny_hook(defn, params):
            return HookDecision(allow=False, reason="Not allowed")

        hooks = ToolHooks()
        hooks.add_pre_hook(deny_hook)
        executor = ToolExecutor(hooks)

        result = await executor.execute(
            tool_def, success_handler, {"input": "test"}
        )

        assert result.status == ToolResultStatus.DENIED
        assert "Not allowed" in result.error_message

    @pytest.mark.asyncio
    async def test_pre_hook_can_modify_params(self, tool_def, success_handler):
        async def modify_hook(defn, params):
            return HookDecision(
                allow=True,
                modified_params={"input": "modified"},
            )

        hooks = ToolHooks()
        hooks.add_pre_hook(modify_hook)
        executor = ToolExecutor(hooks)

        result = await executor.execute(
            tool_def, success_handler, {"input": "original"}
        )

        assert result.status == ToolResultStatus.SUCCESS
        assert result.result == "Result: modified"

    @pytest.mark.asyncio
    async def test_post_hook_called(self, tool_def, success_handler):
        post_hook_called = False

        async def post_hook(defn, params, result):
            nonlocal post_hook_called
            post_hook_called = True

        hooks = ToolHooks()
        hooks.add_post_hook(post_hook)
        executor = ToolExecutor(hooks)

        await executor.execute(tool_def, success_handler, {"input": "test"})

        assert post_hook_called


class TestToolExecutorParamSafety:
    @pytest.fixture
    def strict_tool_def(self):
        return ToolDefinition(
            name="greet",
            description="Greet someone",
            parameters=[
                ToolParameter(
                    name="name",
                    type=ToolParameterType.STRING,
                    description="Name to greet",
                    required=True,
                ),
                ToolParameter(
                    name="greeting",
                    type=ToolParameterType.STRING,
                    description="Greeting prefix",
                    required=False,
                    default="Hello",
                ),
            ],
        )

    @pytest.fixture
    def strict_handler(self):
        async def handler(name: str, greeting: str = "Hello") -> ToolResult:
            return ToolResult.success(f"{greeting}, {name}!")
        return handler

    @pytest.mark.asyncio
    async def test_unknown_params_stripped(self, strict_tool_def, strict_handler):
        executor = ToolExecutor()
        result = await executor.execute(
            strict_tool_def,
            strict_handler,
            {"name": "World", "extra": "should_be_ignored", "another_unknown": True},
        )
        assert result.status == ToolResultStatus.SUCCESS
        assert result.result == "Hello, World!"

    @pytest.mark.asyncio
    async def test_optional_param_default_filled(self, strict_tool_def, strict_handler):
        executor = ToolExecutor()
        result = await executor.execute(
            strict_tool_def,
            strict_handler,
            {"name": "World"},
        )
        assert result.status == ToolResultStatus.SUCCESS
        assert result.result == "Hello, World!"

    @pytest.mark.asyncio
    async def test_optional_param_override(self, strict_tool_def, strict_handler):
        executor = ToolExecutor()
        result = await executor.execute(
            strict_tool_def,
            strict_handler,
            {"name": "World", "greeting": "Hi"},
        )
        assert result.status == ToolResultStatus.SUCCESS
        assert result.result == "Hi, World!"
