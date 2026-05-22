"""Tests for DeepSeek LLM provider - API calls, streaming, error handling."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from lukawi.llm.deepseek import DeepSeekProvider
from lukawi.llm.base import (
    Message, MessageRole, LLMResponse, LLMChunk, TokenUsage,
    ToolCall, FunctionCall, ModelInfo
)
from lukawi.config.models import DeepSeekConfig
from lukawi.tools.base import ToolDefinition, ToolParameter, ToolParameterType


@pytest.fixture
def config():
    return DeepSeekConfig(api_key="test-key", model="deepseek-v4-flash")


@pytest.fixture
def provider(config):
    return DeepSeekProvider(config)


@pytest.fixture
def sample_messages():
    return [
        Message(role=MessageRole.SYSTEM, content="You are helpful."),
        Message(role=MessageRole.USER, content="Hello!")
    ]


@pytest.fixture
def sample_tool():
    return ToolDefinition(
        name="web_fetch",
        description="Fetch URL content",
        parameters=[
            ToolParameter(
                name="url",
                type=ToolParameterType.STRING,
                description="URL to fetch"
            )
        ]
    )


def _make_mock_response(content="OK", tool_calls=None, finish_reason="stop",
                        prompt_tokens=10, completion_tokens=5, total_tokens=15):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    mock_response.choices[0].message.tool_calls = tool_calls
    mock_response.choices[0].finish_reason = finish_reason
    mock_response.usage.prompt_tokens = prompt_tokens
    mock_response.usage.completion_tokens = completion_tokens
    mock_response.usage.total_tokens = total_tokens
    return mock_response


class TestDeepSeekProviderInit:
    def test_init_sets_model(self, provider, config):
        assert provider.model == config.model

    def test_init_sets_config(self, provider, config):
        assert provider.config == config

    def test_init_creates_client(self, provider):
        assert provider.client is not None

    def test_init_custom_base_url(self):
        cfg = DeepSeekConfig(
            api_key="key",
            model="deepseek-pro",
            base_url="https://custom.api.com"
        )
        p = DeepSeekProvider(cfg)
        assert p.model == "deepseek-pro"


class TestGetModelInfo:
    def test_returns_model_info(self, provider):
        info = provider.get_model_info()
        assert isinstance(info, ModelInfo)

    def test_model_name(self, provider):
        info = provider.get_model_info()
        assert info.name == "deepseek-v4-flash"

    def test_provider_name(self, provider):
        info = provider.get_model_info()
        assert info.provider == "deepseek"

    def test_supports_tools(self, provider):
        info = provider.get_model_info()
        assert info.supports_tools is True

    def test_supports_streaming(self, provider):
        info = provider.get_model_info()
        assert info.supports_streaming is True

    def test_max_tokens_from_config(self, provider):
        info = provider.get_model_info()
        assert info.max_tokens == 4096


class TestChatSimple:
    async def test_returns_llm_response(self, provider, sample_messages):
        mock_response = _make_mock_response()
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages)
        assert isinstance(response, LLMResponse)

    async def test_response_content(self, provider, sample_messages):
        mock_response = _make_mock_response(content="Hello! How can I help?")
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages)
        assert response.content == "Hello! How can I help?"

    async def test_no_tool_calls(self, provider, sample_messages):
        mock_response = _make_mock_response()
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages)
        assert response.tool_calls is None

    async def test_finish_reason(self, provider, sample_messages):
        mock_response = _make_mock_response()
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages)
        assert response.finish_reason == "stop"

    async def test_token_usage(self, provider, sample_messages):
        mock_response = _make_mock_response(prompt_tokens=50, completion_tokens=10, total_tokens=60)
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages)
        assert response.usage.prompt_tokens == 50
        assert response.usage.completion_tokens == 10
        assert response.usage.total_tokens == 60

    async def test_passes_messages_to_api(self, provider, sample_messages):
        mock_response = _make_mock_response()
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            await provider.chat(sample_messages)
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["model"] == "deepseek-v4-flash"
        assert len(call_kwargs["messages"]) == 2
        assert call_kwargs["messages"][0]["role"] == "system"
        assert call_kwargs["messages"][1]["role"] == "user"

    async def test_temperature_passed(self, provider, sample_messages):
        mock_response = _make_mock_response()
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            await provider.chat(sample_messages, temperature=0.3)
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["temperature"] == 0.3

    async def test_max_tokens_passed(self, provider, sample_messages):
        mock_response = _make_mock_response()
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            await provider.chat(sample_messages, max_tokens=100)
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["max_tokens"] == 100

    async def test_no_max_tokens_when_none(self, provider, sample_messages):
        mock_response = _make_mock_response()
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            await provider.chat(sample_messages)
        call_kwargs = mock_create.call_args[1]
        assert "max_tokens" not in call_kwargs


class TestChatWithTools:
    async def test_tools_passed_to_api(self, provider, sample_messages, sample_tool):
        mock_response = _make_mock_response()
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            await provider.chat(sample_messages, tools=[sample_tool])
        call_kwargs = mock_create.call_args[1]
        assert "tools" in call_kwargs
        assert len(call_kwargs["tools"]) == 1
        assert call_kwargs["tools"][0]["function"]["name"] == "web_fetch"
        assert call_kwargs["tool_choice"] == "auto"

    async def test_tool_call_response(self, provider, sample_messages, sample_tool):
        mock_tc = MagicMock()
        mock_tc.id = "call_123"
        mock_tc.type = "function"
        mock_tc.function.name = "web_fetch"
        mock_tc.function.arguments = '{"url": "https://example.com"}'
        mock_response = _make_mock_response(
            content=None, tool_calls=[mock_tc], finish_reason="tool_calls",
            prompt_tokens=100, completion_tokens=20, total_tokens=120
        )
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages, tools=[sample_tool])
        assert response.content is None
        assert response.tool_calls is not None
        assert len(response.tool_calls) == 1

    async def test_tool_call_id(self, provider, sample_messages, sample_tool):
        mock_tc = MagicMock()
        mock_tc.id = "call_123"
        mock_tc.type = "function"
        mock_tc.function.name = "web_fetch"
        mock_tc.function.arguments = '{"url": "https://example.com"}'
        mock_response = _make_mock_response(
            content=None, tool_calls=[mock_tc], finish_reason="tool_calls",
            prompt_tokens=100, completion_tokens=20, total_tokens=120
        )
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages, tools=[sample_tool])
        assert response.tool_calls[0].id == "call_123"

    async def test_tool_call_function_name(self, provider, sample_messages, sample_tool):
        mock_tc = MagicMock()
        mock_tc.id = "call_123"
        mock_tc.type = "function"
        mock_tc.function.name = "web_fetch"
        mock_tc.function.arguments = '{"url": "https://example.com"}'
        mock_response = _make_mock_response(
            content=None, tool_calls=[mock_tc], finish_reason="tool_calls",
            prompt_tokens=100, completion_tokens=20, total_tokens=120
        )
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages, tools=[sample_tool])
        assert response.tool_calls[0].function.name == "web_fetch"

    async def test_tool_call_arguments(self, provider, sample_messages, sample_tool):
        mock_tc = MagicMock()
        mock_tc.id = "call_123"
        mock_tc.type = "function"
        mock_tc.function.name = "web_fetch"
        mock_tc.function.arguments = '{"url": "https://example.com"}'
        mock_response = _make_mock_response(
            content=None, tool_calls=[mock_tc], finish_reason="tool_calls",
            prompt_tokens=100, completion_tokens=20, total_tokens=120
        )
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages, tools=[sample_tool])
        assert response.tool_calls[0].function.arguments == '{"url": "https://example.com"}'

    async def test_finish_reason_tool_calls(self, provider, sample_messages, sample_tool):
        mock_tc = MagicMock()
        mock_tc.id = "call_123"
        mock_tc.type = "function"
        mock_tc.function.name = "web_fetch"
        mock_tc.function.arguments = '{"url": "https://example.com"}'
        mock_response = _make_mock_response(
            content=None, tool_calls=[mock_tc], finish_reason="tool_calls",
            prompt_tokens=100, completion_tokens=20, total_tokens=120
        )
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages, tools=[sample_tool])
        assert response.finish_reason == "tool_calls"

    async def test_multiple_tool_calls(self, provider, sample_messages):
        tc1 = MagicMock()
        tc1.id = "call_1"
        tc1.type = "function"
        tc1.function.name = "web_fetch"
        tc1.function.arguments = '{"url": "https://a.com"}'
        tc2 = MagicMock()
        tc2.id = "call_2"
        tc2.type = "function"
        tc2.function.name = "web_fetch"
        tc2.function.arguments = '{"url": "https://b.com"}'
        mock_response = _make_mock_response(
            content=None, tool_calls=[tc1, tc2], finish_reason="tool_calls",
            prompt_tokens=100, completion_tokens=40, total_tokens=140
        )
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages)
        assert response.tool_calls is not None
        assert len(response.tool_calls) == 2
        assert response.tool_calls[0].id == "call_1"
        assert response.tool_calls[1].id == "call_2"


def _make_stream_chunk(content=None, tool_calls=None, finish_reason=None):
    mock_chunk = MagicMock()
    mock_chunk.choices = [MagicMock()]
    mock_chunk.choices[0].delta.content = content
    mock_chunk.choices[0].delta.tool_calls = tool_calls
    mock_chunk.choices[0].finish_reason = finish_reason
    return mock_chunk


def _make_stream_tool_call_chunk(index, tc_id=None, name=None, arguments=None):
    tc = MagicMock()
    tc.index = index
    tc.id = tc_id
    tc.function = MagicMock()
    tc.function.name = name
    tc.function.arguments = arguments
    return [tc]


class TestChatStream:
    async def test_yields_chunks(self, provider, sample_messages):
        mock_chunk = _make_stream_chunk(content="Hello")
        async def mock_stream():
            yield mock_chunk
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_stream()
            chunks = []
            async for chunk in provider.chat_stream(sample_messages):
                chunks.append(chunk)
        assert len(chunks) == 1
        assert isinstance(chunks[0], LLMChunk)

    async def test_stream_content(self, provider, sample_messages):
        mock_chunk = _make_stream_chunk(content="Hello")
        async def mock_stream():
            yield mock_chunk
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_stream()
            chunks = []
            async for chunk in provider.chat_stream(sample_messages):
                chunks.append(chunk)
        assert chunks[0].content == "Hello"

    async def test_stream_multiple_chunks(self, provider, sample_messages):
        chunk1 = _make_stream_chunk(content="Hello")
        chunk2 = _make_stream_chunk(content=" World")
        chunk3 = _make_stream_chunk(content=None, finish_reason="stop")
        async def mock_stream():
            yield chunk1
            yield chunk2
            yield chunk3
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_stream()
            chunks = []
            async for chunk in provider.chat_stream(sample_messages):
                chunks.append(chunk)
        assert len(chunks) == 3
        assert chunks[0].content == "Hello"
        assert chunks[1].content == " World"
        assert chunks[2].finish_reason == "stop"

    async def test_stream_skips_empty_choices(self, provider, sample_messages):
        empty_chunk = MagicMock()
        empty_chunk.choices = []
        content_chunk = _make_stream_chunk(content="OK")
        async def mock_stream():
            yield empty_chunk
            yield content_chunk
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_stream()
            chunks = []
            async for chunk in provider.chat_stream(sample_messages):
                chunks.append(chunk)
        assert len(chunks) == 1
        assert chunks[0].content == "OK"

    async def test_stream_passes_tools(self, provider, sample_messages, sample_tool):
        mock_chunk = _make_stream_chunk(content="OK")
        async def mock_stream():
            yield mock_chunk
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_stream()
            async for _ in provider.chat_stream(sample_messages, tools=[sample_tool]):
                pass
        call_kwargs = mock_create.call_args[1]
        assert "tools" in call_kwargs
        assert call_kwargs["stream"] is True

    async def test_stream_temperature(self, provider, sample_messages):
        mock_chunk = _make_stream_chunk(content="OK")
        async def mock_stream():
            yield mock_chunk
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_stream()
            async for _ in provider.chat_stream(sample_messages, temperature=0.5):
                pass
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["temperature"] == 0.5


class TestChatStreamToolCalls:
    async def test_stream_tool_call_accumulation(self, provider, sample_messages):
        tc_id_chunk = _make_stream_chunk(
            tool_calls=_make_stream_tool_call_chunk(0, tc_id="call_abc", name="web_fetch", arguments="")
        )
        tc_args_chunk = _make_stream_chunk(
            tool_calls=_make_stream_tool_call_chunk(0, arguments='{"url":')
        )
        tc_args_chunk2 = _make_stream_chunk(
            tool_calls=_make_stream_tool_call_chunk(0, arguments=' "https://example.com"}')
        )
        end_chunk = _make_stream_chunk(finish_reason="tool_calls")
        async def mock_stream():
            yield tc_id_chunk
            yield tc_args_chunk
            yield tc_args_chunk2
            yield end_chunk
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_stream()
            chunks = []
            async for chunk in provider.chat_stream(sample_messages):
                chunks.append(chunk)
        tool_call_chunks = [c for c in chunks if c.tool_calls]
        assert len(tool_call_chunks) >= 1
        last_tc_chunk = tool_call_chunks[-1]
        assert last_tc_chunk.tool_calls[0].id == "call_abc"
        assert last_tc_chunk.tool_calls[0].function.name == "web_fetch"
        assert '"url":' in last_tc_chunk.tool_calls[0].function.arguments

    async def test_stream_tool_call_not_emitted_until_id_and_name(self, provider, sample_messages):
        tc_name_chunk = _make_stream_chunk(
            tool_calls=_make_stream_tool_call_chunk(0, tc_id="call_xyz", name=None, arguments="")
        )
        end_chunk = _make_stream_chunk(finish_reason="stop")
        async def mock_stream():
            yield tc_name_chunk
            yield end_chunk
        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_stream()
            chunks = []
            async for chunk in provider.chat_stream(sample_messages):
                chunks.append(chunk)
        tool_call_chunks = [c for c in chunks if c.tool_calls]
        assert len(tool_call_chunks) == 0

    def test_supports_tools(self, provider):
        info = provider.get_model_info()
        assert info.supports_tools is True

    def test_supports_streaming(self, provider):
        info = provider.get_model_info()
        assert info.supports_streaming is True

    def test_max_tokens_from_config(self, provider):
        info = provider.get_model_info()
        assert info.max_tokens == 4096


class TestChatSimple:
    """Test non-streaming chat completions."""

    async def test_returns_llm_response(self, provider, sample_messages):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello! How can I help?"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 60

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages)

        assert isinstance(response, LLMResponse)

    async def test_response_content(self, provider, sample_messages):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello! How can I help?"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 60

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages)

        assert response.content == "Hello! How can I help?"

    async def test_no_tool_calls(self, provider, sample_messages):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hi!"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages)

        assert response.tool_calls is None

    async def test_finish_reason(self, provider, sample_messages):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Done"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages)

        assert response.finish_reason == "stop"

    async def test_token_usage(self, provider, sample_messages):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Done"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 60

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages)

        assert response.usage.prompt_tokens == 50
        assert response.usage.completion_tokens == 10
        assert response.usage.total_tokens == 60

    async def test_passes_messages_to_api(self, provider, sample_messages):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "OK"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            await provider.chat(sample_messages)

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["model"] == "deepseek-v4-flash"
        assert len(call_kwargs["messages"]) == 2
        assert call_kwargs["messages"][0]["role"] == "system"
        assert call_kwargs["messages"][1]["role"] == "user"

    async def test_temperature_passed(self, provider, sample_messages):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "OK"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            await provider.chat(sample_messages, temperature=0.3)

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["temperature"] == 0.3

    async def test_max_tokens_passed(self, provider, sample_messages):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "OK"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            await provider.chat(sample_messages, max_tokens=100)

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["max_tokens"] == 100

    async def test_no_max_tokens_when_none(self, provider, sample_messages):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "OK"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            await provider.chat(sample_messages)

        call_kwargs = mock_create.call_args[1]
        assert "max_tokens" not in call_kwargs


class TestChatWithTools:
    """Test chat completions with tool definitions."""

    async def test_tools_passed_to_api(self, provider, sample_messages, sample_tool):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "OK"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            await provider.chat(sample_messages, tools=[sample_tool])

        call_kwargs = mock_create.call_args[1]
        assert "tools" in call_kwargs
        assert len(call_kwargs["tools"]) == 1
        assert call_kwargs["tools"][0]["function"]["name"] == "web_fetch"
        assert call_kwargs["tool_choice"] == "auto"

    async def test_tool_call_response(self, provider, sample_messages, sample_tool):
        mock_tc = MagicMock()
        mock_tc.id = "call_123"
        mock_tc.type = "function"
        mock_tc.function.name = "web_fetch"
        mock_tc.function.arguments = '{"url": "https://example.com"}'

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_response.choices[0].message.tool_calls = [mock_tc]
        mock_response.choices[0].finish_reason = "tool_calls"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 120

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages, tools=[sample_tool])

        assert response.content is None
        assert response.tool_calls is not None
        assert len(response.tool_calls) == 1

    async def test_tool_call_id(self, provider, sample_messages, sample_tool):
        mock_tc = MagicMock()
        mock_tc.id = "call_123"
        mock_tc.type = "function"
        mock_tc.function.name = "web_fetch"
        mock_tc.function.arguments = '{"url": "https://example.com"}'

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_response.choices[0].message.tool_calls = [mock_tc]
        mock_response.choices[0].finish_reason = "tool_calls"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 120

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages, tools=[sample_tool])

        assert response.tool_calls[0].id == "call_123"

    async def test_tool_call_function_name(self, provider, sample_messages, sample_tool):
        mock_tc = MagicMock()
        mock_tc.id = "call_123"
        mock_tc.type = "function"
        mock_tc.function.name = "web_fetch"
        mock_tc.function.arguments = '{"url": "https://example.com"}'

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_response.choices[0].message.tool_calls = [mock_tc]
        mock_response.choices[0].finish_reason = "tool_calls"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 120

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages, tools=[sample_tool])

        assert response.tool_calls[0].function.name == "web_fetch"

    async def test_tool_call_arguments(self, provider, sample_messages, sample_tool):
        mock_tc = MagicMock()
        mock_tc.id = "call_123"
        mock_tc.type = "function"
        mock_tc.function.name = "web_fetch"
        mock_tc.function.arguments = '{"url": "https://example.com"}'

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_response.choices[0].message.tool_calls = [mock_tc]
        mock_response.choices[0].finish_reason = "tool_calls"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 120

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages, tools=[sample_tool])

        assert response.tool_calls[0].function.arguments == '{"url": "https://example.com"}'

    async def test_finish_reason_tool_calls(self, provider, sample_messages, sample_tool):
        mock_tc = MagicMock()
        mock_tc.id = "call_123"
        mock_tc.type = "function"
        mock_tc.function.name = "web_fetch"
        mock_tc.function.arguments = '{"url": "https://example.com"}'

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_response.choices[0].message.tool_calls = [mock_tc]
        mock_response.choices[0].finish_reason = "tool_calls"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 120

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages, tools=[sample_tool])

        assert response.finish_reason == "tool_calls"

    async def test_multiple_tool_calls(self, provider, sample_messages):
        tc1 = MagicMock()
        tc1.id = "call_1"
        tc1.type = "function"
        tc1.function.name = "web_fetch"
        tc1.function.arguments = '{"url": "https://a.com"}'

        tc2 = MagicMock()
        tc2.id = "call_2"
        tc2.type = "function"
        tc2.function.name = "web_fetch"
        tc2.function.arguments = '{"url": "https://b.com"}'

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_response.choices[0].message.tool_calls = [tc1, tc2]
        mock_response.choices[0].finish_reason = "tool_calls"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 40
        mock_response.usage.total_tokens = 140

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            response = await provider.chat(sample_messages)

        assert response.tool_calls is not None
        assert len(response.tool_calls) == 2
        assert response.tool_calls[0].id == "call_1"
        assert response.tool_calls[1].id == "call_2"


class TestChatStream:
    """Test streaming chat completions."""

    async def test_yields_chunks(self, provider, sample_messages):
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = "Hello"
        mock_chunk.choices[0].delta.tool_calls = None
        mock_chunk.choices[0].finish_reason = None

        async def mock_stream():
            yield mock_chunk

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_stream()
            chunks = []
            async for chunk in provider.chat_stream(sample_messages):
                chunks.append(chunk)

        assert len(chunks) == 1
        assert isinstance(chunks[0], LLMChunk)

    async def test_stream_content(self, provider, sample_messages):
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = "Hello"
        mock_chunk.choices[0].delta.tool_calls = None
        mock_chunk.choices[0].finish_reason = None

        async def mock_stream():
            yield mock_chunk

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_stream()
            chunks = []
            async for chunk in provider.chat_stream(sample_messages):
                chunks.append(chunk)

        assert chunks[0].content == "Hello"

    async def test_stream_multiple_chunks(self, provider, sample_messages):
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta.content = "Hello"
        chunk1.choices[0].delta.tool_calls = None
        chunk1.choices[0].finish_reason = None

        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = " World"
        chunk2.choices[0].delta.tool_calls = None
        chunk2.choices[0].finish_reason = None

        chunk3 = MagicMock()
        chunk3.choices = [MagicMock()]
        chunk3.choices[0].delta.content = None
        chunk3.choices[0].delta.tool_calls = None
        chunk3.choices[0].finish_reason = "stop"

        async def mock_stream():
            yield chunk1
            yield chunk2
            yield chunk3

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_stream()
            chunks = []
            async for chunk in provider.chat_stream(sample_messages):
                chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0].content == "Hello"
        assert chunks[1].content == " World"
        assert chunks[2].finish_reason == "stop"

    async def test_stream_skips_empty_choices(self, provider, sample_messages):
        empty_chunk = MagicMock()
        empty_chunk.choices = []

        content_chunk = MagicMock()
        content_chunk.choices = [MagicMock()]
        content_chunk.choices[0].delta.content = "OK"
        content_chunk.choices[0].delta.tool_calls = None
        content_chunk.choices[0].finish_reason = None

        async def mock_stream():
            yield empty_chunk
            yield content_chunk

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_stream()
            chunks = []
            async for chunk in provider.chat_stream(sample_messages):
                chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0].content == "OK"

    async def test_stream_passes_tools(self, provider, sample_messages, sample_tool):
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = "OK"
        mock_chunk.choices[0].delta.tool_calls = None
        mock_chunk.choices[0].finish_reason = None

        async def mock_stream():
            yield mock_chunk

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_stream()
            async for _ in provider.chat_stream(sample_messages, tools=[sample_tool]):
                pass

        call_kwargs = mock_create.call_args[1]
        assert "tools" in call_kwargs
        assert call_kwargs["stream"] is True

    async def test_stream_temperature(self, provider, sample_messages):
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = "OK"
        mock_chunk.choices[0].delta.tool_calls = None
        mock_chunk.choices[0].finish_reason = None

        async def mock_stream():
            yield mock_chunk

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_stream()
            async for _ in provider.chat_stream(sample_messages, temperature=0.5):
                pass

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["temperature"] == 0.5


class TestChatStreamToolCalls:
    """Test streaming with tool call accumulation."""

    async def test_stream_tool_call_accumulation(self, provider, sample_messages):
        """Tool calls should be accumulated across streaming chunks."""
        tc_id_chunk = MagicMock()
        tc_id_chunk.choices = [MagicMock()]
        tc_id_chunk.choices[0].delta.content = None
        tc_id_chunk.choices[0].delta.tool_calls = [MagicMock()]
        tc_id_chunk.choices[0].delta.tool_calls[0].index = 0
        tc_id_chunk.choices[0].delta.tool_calls[0].id = "call_abc"
        tc_id_chunk.choices[0].delta.tool_calls[0].function = MagicMock()
        tc_id_chunk.choices[0].delta.tool_calls[0].function.name = "web_fetch"
        tc_id_chunk.choices[0].delta.tool_calls[0].function.arguments = ""
        tc_id_chunk.choices[0].finish_reason = None

        tc_args_chunk = MagicMock()
        tc_args_chunk.choices = [MagicMock()]
        tc_args_chunk.choices[0].delta.content = None
        tc_args_chunk.choices[0].delta.tool_calls = [MagicMock()]
        tc_args_chunk.choices[0].delta.tool_calls[0].index = 0
        tc_args_chunk.choices[0].delta.tool_calls[0].id = None
        tc_args_chunk.choices[0].delta.tool_calls[0].function = MagicMock()
        tc_args_chunk.choices[0].delta.tool_calls[0].function.name = None
        tc_args_chunk.choices[0].delta.tool_calls[0].function.arguments = '{"url":'
        tc_args_chunk.choices[0].finish_reason = None

        tc_args_chunk2 = MagicMock()
        tc_args_chunk2.choices = [MagicMock()]
        tc_args_chunk2.choices[0].delta.content = None
        tc_args_chunk2.choices[0].delta.tool_calls = [MagicMock()]
        tc_args_chunk2.choices[0].delta.tool_calls[0].index = 0
        tc_args_chunk2.choices[0].delta.tool_calls[0].id = None
        tc_args_chunk2.choices[0].delta.tool_calls[0].function = MagicMock()
        tc_args_chunk2.choices[0].delta.tool_calls[0].function.name = None
        tc_args_chunk2.choices[0].delta.tool_calls[0].function.arguments = ' "https://example.com"}'
        tc_args_chunk2.choices[0].finish_reason = None

        end_chunk = MagicMock()
        end_chunk.choices = [MagicMock()]
        end_chunk.choices[0].delta.content = None
        end_chunk.choices[0].delta.tool_calls = None
        end_chunk.choices[0].finish_reason = "tool_calls"

        async def mock_stream():
            yield tc_id_chunk
            yield tc_args_chunk
            yield tc_args_chunk2
            yield end_chunk

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_stream()
            chunks = []
            async for chunk in provider.chat_stream(sample_messages):
                chunks.append(chunk)

        # Last chunk with tool calls should have the accumulated result
        tool_call_chunks = [c for c in chunks if c.tool_calls]
        assert len(tool_call_chunks) >= 1
        last_tc_chunk = tool_call_chunks[-1]
        assert last_tc_chunk.tool_calls[0].id == "call_abc"
        assert last_tc_chunk.tool_calls[0].function.name == "web_fetch"
        assert '"url":' in last_tc_chunk.tool_calls[0].function.arguments

    async def test_stream_tool_call_not_emitted_until_id_and_name(self, provider, sample_messages):
        """Tool calls should not be emitted until both id and name are known."""
        tc_name_chunk = MagicMock()
        tc_name_chunk.choices = [MagicMock()]
        tc_name_chunk.choices[0].delta.content = None
        tc_name_chunk.choices[0].delta.tool_calls = [MagicMock()]
        tc_name_chunk.choices[0].delta.tool_calls[0].index = 0
        tc_name_chunk.choices[0].delta.tool_calls[0].id = "call_xyz"
        tc_name_chunk.choices[0].delta.tool_calls[0].function = MagicMock()
        tc_name_chunk.choices[0].delta.tool_calls[0].function.name = None
        tc_name_chunk.choices[0].delta.tool_calls[0].function.arguments = ""
        tc_name_chunk.choices[0].finish_reason = None

        end_chunk = MagicMock()
        end_chunk.choices = [MagicMock()]
        end_chunk.choices[0].delta.content = None
        end_chunk.choices[0].delta.tool_calls = None
        end_chunk.choices[0].finish_reason = "stop"

        async def mock_stream():
            yield tc_name_chunk
            yield end_chunk

        with patch.object(
            provider.client.chat.completions, 'create', new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_stream()
            chunks = []
            async for chunk in provider.chat_stream(sample_messages):
                chunks.append(chunk)

        # No tool calls should be emitted since name is None
        tool_call_chunks = [c for c in chunks if c.tool_calls]
        assert len(tool_call_chunks) == 0
