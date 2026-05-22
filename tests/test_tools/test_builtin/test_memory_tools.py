"""Tests for memory tools registration and handlers."""

from __future__ import annotations

import pytest

from lukawi.tools.base import ToolParameterType, ToolResultStatus
from lukawi.tools.builtin.memory_tools import (
    MEMORY_RECALL_TOOL,
    MEMORY_SAVE_TOOL,
    register_memory_tools,
)
from lukawi.tools.registry import ToolRegistry
from lukawi.llm.base import Message, MessageRole


class TestMemoryToolDefinitions:
    def test_memory_recall_tool_name(self):
        assert MEMORY_RECALL_TOOL.name == "memory_recall"

    def test_memory_recall_tool_has_query_param(self):
        params = {p.name: p for p in MEMORY_RECALL_TOOL.parameters}
        assert "query" in params
        assert params["query"].type == ToolParameterType.STRING

    def test_memory_recall_tool_has_limit_param(self):
        params = {p.name: p for p in MEMORY_RECALL_TOOL.parameters}
        assert "limit" in params
        assert params["limit"].type == ToolParameterType.INTEGER
        assert params["limit"].required is False
        assert params["limit"].default == 5

    def test_memory_save_tool_name(self):
        assert MEMORY_SAVE_TOOL.name == "memory_save"

    def test_memory_save_tool_has_content_param(self):
        params = {p.name: p for p in MEMORY_SAVE_TOOL.parameters}
        assert "content" in params
        assert params["content"].type == ToolParameterType.STRING

    def test_memory_save_tool_has_metadata_param(self):
        params = {p.name: p for p in MEMORY_SAVE_TOOL.parameters}
        assert "metadata_json" in params
        assert params["metadata_json"].required is False
        assert params["metadata_json"].default == "{}"

    def test_memory_recall_category(self):
        assert MEMORY_RECALL_TOOL.category == "memory"

    def test_memory_save_category(self):
        assert MEMORY_SAVE_TOOL.category == "memory"


class TestMemoryToolsRegistration:
    def test_register_with_memory_manager(self):
        registry = ToolRegistry()
        register_memory_tools(registry, memory_manager="not_none")
        assert registry.has("memory_recall")
        assert registry.has("memory_save")

    def test_register_without_memory_manager(self):
        registry = ToolRegistry()
        register_memory_tools(registry, memory_manager=None)
        assert registry.has("memory_recall")
        assert registry.has("memory_save")

    def test_registered_handlers_are_callable(self):
        registry = ToolRegistry()
        register_memory_tools(registry, memory_manager=None)
        _, recall_handler = registry.get("memory_recall")
        _, save_handler = registry.get("memory_save")
        assert callable(recall_handler)
        assert callable(save_handler)


@pytest.mark.asyncio
async def test_recall_without_manager_returns_error():
    registry = ToolRegistry()
    register_memory_tools(registry, memory_manager=None)
    _, handler = registry.get("memory_recall")
    result = await handler(query="test")
    assert result.status == ToolResultStatus.ERROR


@pytest.mark.asyncio
async def test_save_without_manager_returns_error():
    registry = ToolRegistry()
    register_memory_tools(registry, memory_manager=None)
    _, handler = registry.get("memory_save")
    result = await handler(content="test info")
    assert result.status == ToolResultStatus.ERROR


@pytest.mark.asyncio
async def test_recall_searches_session_context_first():
    """memory_recall should find session messages before querying long-term."""
    class FakeSessionManager:
        def __init__(self):
            self._messages_cache = {
                "session-a": [
                    Message(role=MessageRole.USER, content="我的名字是张三"),
                    Message(role=MessageRole.ASSISTANT, content="好的，已记住你叫张三"),
                ],
                "session-b": [
                    Message(role=MessageRole.USER, content="今天天气怎么样"),
                ],
            }

    class FakeMemoryManager:
        def __init__(self):
            self.session_manager = FakeSessionManager()
            self.longterm = None

    registry = ToolRegistry()
    register_memory_tools(registry, memory_manager=FakeMemoryManager())
    _, handler = registry.get("memory_recall")

    result = await handler(query="张三")
    assert result.status == ToolResultStatus.SUCCESS
    assert result.result is not None
    assert len(result.result) >= 1
    assert result.result[0]["type"] == "session"
    assert "张三" in result.result[0]["content"]


@pytest.mark.asyncio
async def test_recall_skips_irrelevant_session():
    """memory_recall should NOT return session messages that don't match the query."""
    class FakeSessionManager:
        def __init__(self):
            self._messages_cache = {
                "session-a": [
                    Message(role=MessageRole.USER, content="今天天气怎么样"),
                ],
            }

    class FakeMemoryManager:
        def __init__(self):
            self.session_manager = FakeSessionManager()
            self.longterm = None

    registry = ToolRegistry()
    register_memory_tools(registry, memory_manager=FakeMemoryManager())
    _, handler = registry.get("memory_recall")

    result = await handler(query="张三")
    assert result.status == ToolResultStatus.SUCCESS
    assert result.result is None or len(result.result) == 0


@pytest.mark.asyncio
async def test_recall_enforces_limit():
    """memory_recall should respect the limit parameter for session results."""
    class FakeSessionManager:
        def __init__(self):
            self._messages_cache = {
                "session-a": [
                    Message(role=MessageRole.USER, content="我喜欢红色"),
                    Message(role=MessageRole.ASSISTANT, content="好的，红色"),
                    Message(role=MessageRole.USER, content="我喜欢蓝色"),
                    Message(role=MessageRole.ASSISTANT, content="好的，蓝色"),
                ],
            }

    class FakeMemoryManager:
        def __init__(self):
            self.session_manager = FakeSessionManager()
            self.longterm = None

    registry = ToolRegistry()
    register_memory_tools(registry, memory_manager=FakeMemoryManager())
    _, handler = registry.get("memory_recall")

    result = await handler(query="喜欢", limit=2)
    assert result.status == ToolResultStatus.SUCCESS
    assert result.metadata is not None
    assert result.metadata.get("count", 0) <= 2


@pytest.mark.asyncio
async def test_recall_falls_back_to_longterm():
    """memory_recall should search long-term when session has no match."""
    class FakeSessionManager:
        def __init__(self):
            self._messages_cache = {
                "session-a": [
                    Message(role=MessageRole.USER, content="今天天气怎么样"),
                ],
            }

    class FakeLongTerm:
        async def search(self, query, user_id="default", limit=5):
            return []

    class FakeMemoryManager:
        def __init__(self):
            self.session_manager = FakeSessionManager()
            self.longterm = FakeLongTerm()

        async def recall(self, query, user_id="default", limit=5):
            if self.longterm:
                return await self.longterm.search(query=query, user_id=user_id, limit=limit)
            return []

    registry = ToolRegistry()
    register_memory_tools(registry, memory_manager=FakeMemoryManager())
    _, handler = registry.get("memory_recall")

    result = await handler(query="张三")
    assert result.status == ToolResultStatus.SUCCESS
