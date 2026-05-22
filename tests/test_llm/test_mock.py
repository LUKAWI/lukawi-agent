"""Tests for Mock LLM provider."""

import pytest
from lukawi.llm.mock import MockProvider
from lukawi.llm.base import Message, MessageRole, LLMResponse, LLMChunk, TokenUsage


@pytest.fixture
def mock_provider():
    return MockProvider()


@pytest.fixture
def sample_messages():
    return [
        Message(role=MessageRole.USER, content="Hello!")
    ]


class TestMockProvider:
    @pytest.mark.asyncio
    async def test_default_response(self, mock_provider, sample_messages):
        response = await mock_provider.chat(sample_messages)

        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert "Hello!" in response.content
        assert mock_provider.call_count == 1

    @pytest.mark.asyncio
    async def test_predefined_responses(self):
        responses = [
            LLMResponse(content="First response"),
            LLMResponse(content="Second response"),
        ]
        provider = MockProvider(responses=responses)

        r1 = await provider.chat([Message(role=MessageRole.USER, content="test")])
        r2 = await provider.chat([Message(role=MessageRole.USER, content="test")])

        assert r1.content == "First response"
        assert r2.content == "Second response"
        assert provider.call_count == 2

    @pytest.mark.asyncio
    async def test_response_cycling(self):
        responses = [LLMResponse(content="A"), LLMResponse(content="B")]
        provider = MockProvider(responses=responses)

        r1 = await provider.chat([Message(role=MessageRole.USER, content="test")])
        r2 = await provider.chat([Message(role=MessageRole.USER, content="test")])
        r3 = await provider.chat([Message(role=MessageRole.USER, content="test")])

        assert r1.content == "A"
        assert r2.content == "B"
        assert r3.content == "A"  # Cycles back

    @pytest.mark.asyncio
    async def test_call_history(self, mock_provider, sample_messages):
        await mock_provider.chat(sample_messages)
        await mock_provider.chat(sample_messages)

        assert len(mock_provider.call_history) == 2
        assert mock_provider.call_history[0] == sample_messages

    @pytest.mark.asyncio
    async def test_stream(self, mock_provider, sample_messages):
        chunks = []
        async for chunk in mock_provider.chat_stream(sample_messages):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert all(isinstance(c, LLMChunk) for c in chunks)
        assert chunks[-1].finish_reason == "stop"

    def test_reset(self, mock_provider):
        mock_provider.call_count = 5
        mock_provider.call_history.append([])

        mock_provider.reset()

        assert mock_provider.call_count == 0
        assert len(mock_provider.call_history) == 0

    def test_get_model_info(self, mock_provider):
        info = mock_provider.get_model_info()
        assert info.name == "mock"
        assert info.provider == "mock"
