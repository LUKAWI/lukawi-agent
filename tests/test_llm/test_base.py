"""Tests for LLM base types."""

import pytest
from lukawi.llm.base import (
    MessageRole, Message, FunctionCall, ToolCall,
    TokenUsage, LLMResponse, LLMChunk, ModelInfo
)


class TestMessageRole:
    def test_roles(self):
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.TOOL.value == "tool"


class TestMessage:
    def test_system_message(self):
        msg = Message(role=MessageRole.SYSTEM, content="You are helpful")
        d = msg.to_dict()
        assert d == {"role": "system", "content": "You are helpful"}

    def test_user_message(self):
        msg = Message(role=MessageRole.USER, content="Hello")
        d = msg.to_dict()
        assert d == {"role": "user", "content": "Hello"}

    def test_assistant_with_tool_calls(self):
        msg = Message(
            role=MessageRole.ASSISTANT,
            tool_calls=[
                ToolCall(
                    id="call_123",
                    function=FunctionCall(
                        name="web_fetch",
                        arguments='{"url": "https://example.com"}'
                    )
                )
            ]
        )
        d = msg.to_dict()
        assert d["role"] == "assistant"
        assert len(d["tool_calls"]) == 1
        assert d["tool_calls"][0]["function"]["name"] == "web_fetch"

    def test_tool_response(self):
        msg = Message(
            role=MessageRole.TOOL,
            content='{"result": "success"}',
            tool_call_id="call_123"
        )
        d = msg.to_dict()
        assert d["role"] == "tool"
        assert d["tool_call_id"] == "call_123"

    def test_assistant_with_reasoning_content(self):
        msg = Message(
            role=MessageRole.ASSISTANT,
            content="Final answer",
            reasoning_content="I need to think about this..."
        )
        d = msg.to_dict()
        assert d["role"] == "assistant"
        assert d["content"] == "Final answer"
        assert d["reasoning_content"] == "I need to think about this..."

    def test_reasoning_content_omitted_when_none(self):
        msg = Message(role=MessageRole.ASSISTANT, content="No reasoning")
        d = msg.to_dict()
        assert "reasoning_content" not in d

    def test_reasoning_content_with_tool_calls(self):
        msg = Message(
            role=MessageRole.ASSISTANT,
            tool_calls=[
                ToolCall(
                    id="call_1",
                    function=FunctionCall(
                        name="web_fetch",
                        arguments='{"url": "https://example.com"}'
                    )
                )
            ],
            reasoning_content="I need to fetch a URL"
        )
        d = msg.to_dict()
        assert d["reasoning_content"] == "I need to fetch a URL"
        assert len(d["tool_calls"]) == 1


class TestLLMResponse:
    def test_content_response(self):
        resp = LLMResponse(content="Hello!")
        assert resp.content == "Hello!"
        assert resp.tool_calls is None
        assert resp.finish_reason == "stop"

    def test_tool_call_response(self):
        resp = LLMResponse(
            tool_calls=[
                ToolCall(
                    id="call_456",
                    function=FunctionCall(
                        name="exec_command",
                        arguments='{"command": "ls"}'
                    )
                )
            ],
            finish_reason="tool_calls"
        )
        assert resp.content is None
        assert len(resp.tool_calls) == 1
        assert resp.finish_reason == "tool_calls"

    def test_reasoning_content(self):
        resp = LLMResponse(
            content=None,
            reasoning_content="I need to search the web first",
            tool_calls=[
                ToolCall(
                    id="call_1",
                    function=FunctionCall(
                        name="web_fetch",
                        arguments='{"url": "https://example.com"}'
                    )
                )
            ],
            finish_reason="tool_calls"
        )
        assert resp.reasoning_content == "I need to search the web first"
        assert resp.content is None
        assert len(resp.tool_calls) == 1


class TestLLMChunk:
    def test_content_chunk(self):
        chunk = LLMChunk(content="Hello", finish_reason=None)
        assert chunk.content == "Hello"
        assert chunk.reasoning_content is None

    def test_reasoning_content_chunk(self):
        chunk = LLMChunk(
            content=None,
            reasoning_content="Thinking step by step",
            finish_reason=None
        )
        assert chunk.reasoning_content == "Thinking step by step"
        assert chunk.content is None

    def test_tool_call_chunk_with_reasoning(self):
        chunk = LLMChunk(
            tool_calls=[
                ToolCall(
                    id="call_1",
                    function=FunctionCall(
                        name="web_fetch",
                        arguments='{"url": "https://example.com"}'
                    )
                )
            ],
            reasoning_content="I need to fetch",
            finish_reason="tool_calls"
        )
        assert chunk.reasoning_content == "I need to fetch"
        assert len(chunk.tool_calls) == 1


class TestTokenUsage:
    def test_default(self):
        usage = TokenUsage()
        assert usage.prompt_tokens == 0
        assert usage.total_tokens == 0

    def test_custom(self):
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50)
        assert usage.total_tokens == 0  # Not auto-calculated
