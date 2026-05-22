"""Tests for tool abstractions."""

import pytest
from lukawi.tools.base import (
    ToolParameterType, ToolParameter, ToolDefinition,
    ToolResultStatus, ToolResult
)


class TestToolParameterType:
    def test_all_types(self):
        assert ToolParameterType.STRING.value == "string"
        assert ToolParameterType.NUMBER.value == "number"
        assert ToolParameterType.INTEGER.value == "integer"
        assert ToolParameterType.BOOLEAN.value == "boolean"
        assert ToolParameterType.ARRAY.value == "array"
        assert ToolParameterType.OBJECT.value == "object"


class TestToolDefinition:
    def test_create_minimal(self):
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool"
        )
        assert tool.name == "test_tool"
        assert tool.parameters == []
        assert tool.category == "general"
    
    def test_to_openai_schema(self):
        tool = ToolDefinition(
            name="web_fetch",
            description="Fetch content from URL",
            parameters=[
                ToolParameter(
                    name="url",
                    type=ToolParameterType.STRING,
                    description="URL to fetch"
                ),
                ToolParameter(
                    name="timeout",
                    type=ToolParameterType.NUMBER,
                    description="Timeout in seconds",
                    required=False,
                    default=30
                )
            ]
        )
        schema = tool.to_openai_schema()
        
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "web_fetch"
        assert "url" in schema["function"]["parameters"]["properties"]
        assert "url" in schema["function"]["parameters"]["required"]
        assert "timeout" not in schema["function"]["parameters"]["required"]


class TestToolResult:
    def test_success(self):
        result = ToolResult.success({"data": "test"})
        assert result.status == ToolResultStatus.SUCCESS
        assert result.result == {"data": "test"}
        assert result.error_message is None
    
    def test_error(self):
        result = ToolResult.error("Something went wrong")
        assert result.status == ToolResultStatus.ERROR
        assert result.error_message == "Something went wrong"
    
    def test_timeout(self):
        result = ToolResult.timeout()
        assert result.status == ToolResultStatus.TIMEOUT
        assert "timeout" in result.error_message.lower()
    
    def test_denied(self):
        result = ToolResult.denied("Not allowed")
        assert result.status == ToolResultStatus.DENIED
        assert result.error_message == "Not allowed"
