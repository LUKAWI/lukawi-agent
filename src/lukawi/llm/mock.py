"""Mock LLM provider for testing."""

from __future__ import annotations

from typing import AsyncGenerator

from lukawi.llm.base import (
    LLMProvider, LLMResponse, LLMChunk, Message, ModelInfo, TokenUsage
)
from lukawi.tools.base import ToolDefinition


class MockProvider(LLMProvider):

    def __init__(
        self,
        responses: list[LLMResponse] | None = None,
        delay: float = 0.0
    ):
        self.responses = responses or []
        self.delay = delay
        self.call_count = 0
        self.call_history: list[list[Message]] = []

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None
    ) -> LLMResponse:
        self.call_history.append(messages)
        self.call_count += 1

        if self.delay > 0:
            import asyncio
            await asyncio.sleep(self.delay)

        if self.responses:
            idx = (self.call_count - 1) % len(self.responses)
            return self.responses[idx]

        last_message = messages[-1] if messages else None

        if last_message and last_message.role.value == "user":
            return LLMResponse(
                content=f"Mock response to: {last_message.content}",
                usage=TokenUsage(
                    prompt_tokens=10,
                    completion_tokens=5,
                    total_tokens=15
                )
            )

        return LLMResponse(
            content="I'm a mock assistant. How can I help?",
            usage=TokenUsage(
                prompt_tokens=5,
                completion_tokens=10,
                total_tokens=15
            )
        )

    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None
    ) -> AsyncGenerator[LLMChunk, None]:
        response = await self.chat(messages, tools, temperature, max_tokens)

        if response.content:
            words = response.content.split()
            for i, word in enumerate(words):
                yield LLMChunk(
                    content=word + (" " if i < len(words) - 1 else ""),
                    finish_reason="stop" if i == len(words) - 1 else None,
                    reasoning_content=response.reasoning_content if i == 0 else None,
                )
        elif response.tool_calls:
            yield LLMChunk(
                tool_calls=response.tool_calls,
                finish_reason="tool_calls",
                reasoning_content=response.reasoning_content,
            )

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(
            name="mock",
            provider="mock",
            max_tokens=4096,
            supports_tools=True,
            supports_streaming=True
        )

    def reset(self) -> None:
        self.call_count = 0
        self.call_history.clear()

    def set_responses(self, responses: list[LLMResponse]) -> None:
        self.responses = responses
        self.call_count = 0
