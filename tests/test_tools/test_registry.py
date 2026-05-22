"""Tests for tool registry."""

import pytest
from lukawi.tools.registry import (
    ToolRegistry, ToolNotFoundError, ToolAlreadyRegisteredError
)
from lukawi.tools.base import ToolDefinition, ToolResult, ToolParameter, ToolParameterType


@pytest.fixture
def registry():
    return ToolRegistry()


@pytest.fixture
def sample_tool():
    return ToolDefinition(
        name="test_tool",
        description="A test tool",
        parameters=[
            ToolParameter(
                name="input",
                type=ToolParameterType.STRING,
                description="Input value"
            )
        ]
    )


@pytest.fixture
def sample_handler():
    async def handler(input: str) -> ToolResult:
        return ToolResult.success(f"Got: {input}")
    return handler


class TestToolRegistry:
    def test_register(self, registry, sample_tool, sample_handler):
        registry.register(sample_tool, sample_handler)
        
        assert registry.has("test_tool")
        assert registry.count == 1
    
    def test_register_duplicate_raises(self, registry, sample_tool, sample_handler):
        registry.register(sample_tool, sample_handler)
        
        with pytest.raises(ToolAlreadyRegisteredError):
            registry.register(sample_tool, sample_handler)
    
    def test_get(self, registry, sample_tool, sample_handler):
        registry.register(sample_tool, sample_handler)
        
        defn, handler = registry.get("test_tool")
        assert defn == sample_tool
        assert handler == sample_handler
    
    def test_get_not_found_raises(self, registry):
        with pytest.raises(ToolNotFoundError):
            registry.get("nonexistent")
    
    def test_list_tools(self, registry, sample_tool, sample_handler):
        registry.register(sample_tool, sample_handler)
        
        tools = registry.list_tools()
        assert len(tools) == 1
        assert tools[0] == sample_tool
    
    def test_has(self, registry):
        assert not registry.has("test_tool")
        
    def test_to_openai_schema(self, registry, sample_tool, sample_handler):
        registry.register(sample_tool, sample_handler)
        
        schemas = registry.to_openai_schema()
        assert len(schemas) == 1
        assert schemas[0]["type"] == "function"
        assert schemas[0]["function"]["name"] == "test_tool"
    
    def test_clear(self, registry, sample_tool, sample_handler):
        registry.register(sample_tool, sample_handler)
        assert registry.count == 1
        
        registry.clear()
        assert registry.count == 0
        assert not registry.has("test_tool")
    
    def test_register_decorator(self, registry, sample_tool):
        @registry.register_decorator(sample_tool)
        async def my_handler(input: str) -> ToolResult:
            return ToolResult.success(input)
        
        assert registry.has("test_tool")
        defn, handler = registry.get("test_tool")
        assert defn == sample_tool

    def test_unregister(self, registry, sample_tool, sample_handler):
        registry.register(sample_tool, sample_handler)
        assert registry.has("test_tool")
        assert registry.count == 1

        registry.unregister("test_tool")

        assert not registry.has("test_tool")
        assert registry.count == 0

    def test_unregister_not_found_raises(self, registry):
        with pytest.raises(ToolNotFoundError):
            registry.unregister("nonexistent")

    def test_unregister_and_reregister(self, registry, sample_tool, sample_handler):
        registry.register(sample_tool, sample_handler)
        assert registry.count == 1

        registry.unregister("test_tool")
        assert registry.count == 0

        registry.register(sample_tool, sample_handler)
        assert registry.count == 1
        assert registry.has("test_tool")
