"""DeepSeek LLM provider implementation."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import AsyncGenerator, Any

from openai import (
    AsyncOpenAI,
    APITimeoutError, RateLimitError, AuthenticationError,
    APIConnectionError, OpenAIError,
)

from lukawi.llm.base import (
    LLMProvider, LLMResponse, LLMChunk, Message, ModelInfo,
    TokenUsage, ToolCall, FunctionCall,
    LLMError, LLMAuthError, LLMRateLimitError, LLMTimeoutError, LLMConnectionError,
)
from lukawi.tools.base import ToolDefinition
from lukawi.config.models import DeepSeekConfig

logger = logging.getLogger("lukawi.llm.deepseek")


class DeepSeekProvider(LLMProvider):

    def __init__(self, config: DeepSeekConfig, timeout: int = 120):
        self.config = config
        self.timeout = timeout
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=timeout,
        )
        self.model = config.model

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None
    ) -> LLMResponse:
        api_messages = [msg.to_dict() for msg in messages]
        last_user = api_messages[-1].get("content", "")[:80] if api_messages else ""
        tool_count = len(tools) if tools else 0

        logger.info(
            "[DeepSeek] → chat model=%s messages=%d tools=%d user=\"%s\"",
            self.model, len(api_messages), tool_count, last_user,
        )
        start = time.monotonic()

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": api_messages,
            "temperature": temperature,
        }

        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        if tools:
            kwargs["tools"] = [tool.to_openai_schema() for tool in tools]
            kwargs["tool_choice"] = "auto"

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(**kwargs)
            except RateLimitError as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning(
                        "[DeepSeek] rate limit hit, retrying in %ds (attempt %d/%d)",
                        wait, attempt + 1, max_retries,
                    )
                    await asyncio.sleep(wait)
                    continue
                raise LLMRateLimitError(str(e)) from e
            except APITimeoutError as e:
                raise LLMTimeoutError(str(e)) from e
            except AuthenticationError as e:
                raise LLMAuthError(str(e)) from e
            except APIConnectionError as e:
                raise LLMConnectionError(str(e)) from e
            except OpenAIError as e:
                raise LLMError(str(e)) from e

        elapsed = time.monotonic() - start
        choice = response.choices[0]
        message = choice.message
        usage = response.usage

        logger.info(
            "[DeepSeek] ← chat finish=%s tokens=%d→%d (%d) duration=%.1fs",
            choice.finish_reason,
            usage.prompt_tokens if usage else 0,
            usage.completion_tokens if usage else 0,
            usage.total_tokens if usage else 0,
            elapsed,
        )

        reasoning_content = getattr(message, "reasoning_content", None)
        if reasoning_content:
            logger.info(
                "[DeepSeek] ← reasoning_content chars=%d",
                len(reasoning_content),
            )

        tool_calls = None
        if message.tool_calls:
            tool_names = [tc.function.name for tc in message.tool_calls]
            logger.info(
                "[DeepSeek] ← tool_calls=%s args=%s",
                tool_names,
                [tc.function.arguments[:100] for tc in message.tool_calls],
            )
            tool_calls = [
                ToolCall(
                    id=tc.id,
                    type=tc.type,
                    function=FunctionCall(
                        name=tc.function.name,
                        arguments=tc.function.arguments
                    )
                )
                for tc in message.tool_calls
            ]

        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
            usage=TokenUsage(
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
            ),
            finish_reason=choice.finish_reason or "stop",
            raw_response=response,
            reasoning_content=reasoning_content,
        )

    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None
    ) -> AsyncGenerator[LLMChunk, None]:
        api_messages = [msg.to_dict() for msg in messages]
        last_user = api_messages[-1].get("content", "")[:80] if api_messages else ""
        tool_count = len(tools) if tools else 0

        logger.info(
            "[DeepSeek] → stream model=%s messages=%d tools=%d user=\"%s\"",
            self.model, len(api_messages), tool_count, last_user,
        )
        start = time.monotonic()

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": api_messages,
            "temperature": temperature,
            "stream": True,
        }

        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        if tools:
            kwargs["tools"] = [tool.to_openai_schema() for tool in tools]
            kwargs["tool_choice"] = "auto"

        tool_call_chunks: dict[int, dict[str, str]] = {}

        try:
            stream = await self.client.chat.completions.create(**kwargs)
        except APITimeoutError as e:
            raise LLMTimeoutError(str(e)) from e
        except RateLimitError as e:
            raise LLMRateLimitError(str(e)) from e
        except AuthenticationError as e:
            raise LLMAuthError(str(e)) from e
        except APIConnectionError as e:
            raise LLMConnectionError(str(e)) from e
        except OpenAIError as e:
            raise LLMError(str(e)) from e

        content_len = 0
        finish = None
        try:
            async for chunk in stream:
                if not chunk.choices:
                    continue

                choice = chunk.choices[0]
                delta = choice.delta

                content = delta.content
                if content:
                    content_len += len(content)

                reasoning_content = getattr(delta, "reasoning_content", None)

                tool_calls = None
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_call_chunks:
                            tool_call_chunks[idx] = {"id": "", "name": "", "arguments": ""}

                        if tc.id:
                            tool_call_chunks[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                tool_call_chunks[idx]["name"] = tc.function.name
                            if tc.function.arguments:
                                tool_call_chunks[idx]["arguments"] += tc.function.arguments

                    tool_calls = [
                        ToolCall(
                            id=tc["id"],
                            type="function",
                            function=FunctionCall(
                                name=tc["name"],
                                arguments=tc["arguments"]
                            )
                        )
                        for tc in tool_call_chunks.values()
                        if tc["id"] and tc["name"]
                    ]

                if choice.finish_reason:
                    finish = choice.finish_reason

                yield LLMChunk(
                    content=content,
                    tool_calls=tool_calls,
                    finish_reason=choice.finish_reason,
                    reasoning_content=reasoning_content,
                )
        except OpenAIError as e:
            raise LLMError(str(e)) from e

        elapsed = time.monotonic() - start
        if tool_call_chunks:
            logger.info(
                "[DeepSeek] ← stream done tool_calls=%d names=%s duration=%.1fs",
                len(tool_call_chunks),
                [v["name"] for v in tool_call_chunks.values()],
                elapsed,
            )
        else:
            logger.info(
                "[DeepSeek] ← stream done chars=%d finish=%s duration=%.1fs",
                content_len, finish, elapsed,
            )

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(
            name=self.model,
            provider="deepseek",
            max_tokens=self.config.max_tokens,
            supports_tools=True,
            supports_streaming=True,
            display_name=getattr(self.config, 'name', '')
        )
