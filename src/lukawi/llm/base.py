"""LLM provider base interface for Lukawi Agent Framework."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator

from lukawi.tools.base import ToolDefinition


class LLMError(Exception):
    """Base exception for all LLM-related errors."""

class LLMAuthError(LLMError):
    """Authentication/API key error."""

class LLMRateLimitError(LLMError):
    """API rate limit exceeded."""

class LLMTimeoutError(LLMError):
    """LLM API request timed out."""

class LLMConnectionError(LLMError):
    """Connection error to LLM API."""


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class FunctionCall:
    name: str
    arguments: str


@dataclass
class ToolCall:
    id: str
    type: str = "function"
    function: FunctionCall = field(default_factory=lambda: FunctionCall(name="", arguments=""))


@dataclass
class Message:
    role: MessageRole
    content: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] | None = None
    name: str | None = None
    reasoning_content: str | None = None

    def to_dict(self) -> dict[str, Any]:
        msg: dict[str, Any] = {"role": self.role.value}

        if self.content is not None:
            msg["content"] = self.content

        if self.tool_call_id is not None:
            msg["tool_call_id"] = self.tool_call_id

        if self.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in self.tool_calls
            ]

        if self.name is not None:
            msg["name"] = self.name

        if self.reasoning_content is not None:
            msg["reasoning_content"] = self.reasoning_content

        return msg


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LLMResponse:
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    usage: TokenUsage = field(default_factory=TokenUsage)
    finish_reason: str = "stop"
    raw_response: Any = None
    reasoning_content: str | None = None


@dataclass
class LLMChunk:
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    finish_reason: str | None = None
    reasoning_content: str | None = None


@dataclass
class ModelInfo:
    name: str
    provider: str
    max_tokens: int = 4096
    supports_tools: bool = True
    supports_streaming: bool = True
    display_name: str = ""  # Optional display name for custom models


class LLMProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[LLMChunk, None]:
        ...

    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        ...
