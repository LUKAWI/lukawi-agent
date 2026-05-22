"""End-to-end integration tests for Lukawi Agent Framework."""

import os
import pytest

from lukawi.config.models import DeepSeekConfig
from lukawi.llm.deepseek import DeepSeekProvider
from lukawi.llm.base import Message, MessageRole
from lukawi.tools.registry import ToolRegistry
from lukawi.tools.builtin.web_fetch import register_web_fetch
from lukawi.tools.builtin.file_ops import register_file_ops
from lukawi.agent.core import ReActAgent, AgentConfig
from lukawi.tools.executor import ToolExecutor
from lukawi.tools.base import ToolDefinition, ToolParameter, ToolParameterType

API_KEY = os.environ.get("DEEPSEEK_API_KEY")
has_api_key = bool(API_KEY)


@pytest.mark.skipif(not has_api_key, reason="DEEPSEEK_API_KEY not set")
class TestEndToEnd:
    """Full end-to-end tests with real DeepSeek API."""

    @pytest.fixture
    def provider(self):
        return DeepSeekProvider(DeepSeekConfig(api_key=API_KEY, model="deepseek-v4-flash"))

    @pytest.fixture
    def tool_registry(self):
        reg = ToolRegistry()
        register_web_fetch(reg)
        register_file_ops(reg)
        return reg

    @pytest.mark.asyncio
    async def test_simple_chat(self, provider):
        """Test basic API call."""
        messages = [Message(role=MessageRole.USER, content="Say 'Hello from Lukawi!' and nothing else.")]
        response = await provider.chat(messages)
        assert response.content is not None
        assert "Lukawi" in response.content
        assert response.finish_reason == "stop"
        assert response.usage.total_tokens > 0
        print(f"\n[Chat] Response: {response.content}")
        print(f"[Chat] Tokens: {response.usage}")

    @pytest.mark.asyncio
    async def test_tool_call_capability(self, provider):
        """Test LLM recognizes tool calling."""
        tools = [ToolDefinition(
            name="web_fetch", description="Fetch content from a URL",
            parameters=[ToolParameter(name="url", type=ToolParameterType.STRING, description="URL to fetch")]
        )]
        messages = [Message(role=MessageRole.USER, content="What would you use to fetch https://example.com?")]
        response = await provider.chat(messages, tools=tools)
        print(f"\n[Tool Call] Response: {response}")
        if response.tool_calls:
            print(f"[Tool Call] Tool selected: {response.tool_calls[0].function.name}")
            assert response.tool_calls[0].function.name == "web_fetch"

    @pytest.mark.asyncio
    async def test_full_agent_reply(self, provider, tool_registry):
        """Test agent responds coherently."""
        agent = ReActAgent(llm=provider, tools=tool_registry, executor=ToolExecutor(), config=AgentConfig(max_steps=5))
        events = []
        async for event in agent.run("What is 2+2? Give only the number."):
            events.append(event)
        final = next((e for e in events if e.type.name == "FINAL_ANSWER"), None)
        assert final is not None
        content = final.data.get("content", "")
        print(f"\n[Agent] Response: {content}")
        assert "4" in content or "four" in content.lower()

    @pytest.mark.asyncio
    async def test_streaming_chat(self, provider):
        """Test streaming API."""
        messages = [Message(role=MessageRole.USER, content="Count from 1 to 3, with a space between each number.")]
        chunks = []
        async for chunk in provider.chat_stream(messages):
            if chunk.content:
                chunks.append(chunk.content)
        full_text = "".join(chunks)
        print(f"\n[Stream] Got {len(chunks)} chunks: {full_text}")
        assert len(chunks) > 0
        assert len(full_text) > 0
