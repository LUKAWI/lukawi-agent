"""Comprehensive integration tests: Agent + Tools + Memory + Skills.

Uses MockProvider so no API key needed. Tests full ReAct loop with
tool calls, memory save/recall, skill trigger matching, and streaming.
"""

import json
import asyncio
import pytest

from lukawi.agent.core import ReActAgent, AgentConfig, AgentEventType
from lukawi.llm.base import LLMResponse, ToolCall, FunctionCall, Message, MessageRole
from lukawi.llm.mock import MockProvider
from lukawi.tools.base import ToolDefinition, ToolResult, ToolResultStatus, ToolParameter, ToolParameterType
from lukawi.tools.registry import ToolRegistry
from lukawi.tools.executor import ToolExecutor
from lukawi.tools.builtin.web_fetch import register_web_fetch
from lukawi.tools.builtin.file_ops import register_file_ops
from lukawi.tools.builtin.shell import register_shell
from lukawi.tools.builtin.memory_tools import register_memory_tools
from lukawi.memory.manager import MemoryManager
from lukawi.skills.loader import SkillLoader, Skill


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def full_tool_registry():
    """ToolRegistry with all builtin tools registered (mock HTTP for web_fetch)."""
    registry = ToolRegistry()
    register_web_fetch(registry)
    register_file_ops(registry)
    register_shell(registry)
    return registry


@pytest.fixture
def memory_manager():
    """In-memory MemoryManager for tests."""
    return MemoryManager(db_path=":memory:", session_max_messages=100)


@pytest.fixture
def sample_skills():
    """Sample skills for trigger matching tests."""
    return [
        Skill(
            name="code_review",
            description="Review code for quality and bugs",
            instructions="Analyze code for bugs, style issues, and improvements.",
            triggers=["review", "code review", "check my code"],
        ),
    ]


# ---------------------------------------------------------------------------
# Simple Chat via Agent
# ---------------------------------------------------------------------------

class TestSimpleChat:
    async def test_agent_responds_directly(self, full_tool_registry):
        """Agent responds with final answer when no tool needed."""
        llm = MockProvider(responses=[
            LLMResponse(content="Hello! I'm Lukawi, your AI assistant.")
        ])
        agent = ReActAgent(llm=llm, tools=full_tool_registry, config=AgentConfig(max_steps=3))

        events = []
        async for event in agent.run("Who are you?"):
            events.append(event)

        thinking = [e for e in events if e.type == AgentEventType.THINKING]
        final = [e for e in events if e.type == AgentEventType.FINAL_ANSWER]
        assert len(thinking) >= 1
        assert len(final) == 1
        assert "Lukawi" in final[0].data.get("content", "")

    async def test_agent_streaming_events_emitted(self, full_tool_registry):
        """Agent emits THINKING and FINAL_ANSWER events in sequence."""
        llm = MockProvider(responses=[
            LLMResponse(content="This is a test response.")
        ])
        agent = ReActAgent(llm=llm, tools=full_tool_registry, config=AgentConfig(max_steps=3))

        event_types = []
        async for event in agent.run("test"):
            event_types.append(event.type)

        assert AgentEventType.THINKING in event_types
        assert AgentEventType.FINAL_ANSWER in event_types
        # THINKING should come before FINAL_ANSWER
        think_idx = event_types.index(AgentEventType.THINKING)
        final_idx = event_types.index(AgentEventType.FINAL_ANSWER)
        assert think_idx < final_idx


# ---------------------------------------------------------------------------
# Tool Calls
# ---------------------------------------------------------------------------

class TestAgentToolCalls:
    async def test_agent_calls_tool_and_returns_result(self, full_tool_registry):
        """Agent calls a tool, gets result, returns final answer."""
        tool_call = ToolCall(
            id="call_1",
            type="function",
            function=FunctionCall(
                name="read_file",
                arguments=json.dumps({"path": "/tmp/test.txt"}),
            ),
        )
        llm = MockProvider(responses=[
            LLMResponse(tool_calls=[tool_call]),
            LLMResponse(content="I read the file for you."),
        ])
        agent = ReActAgent(llm=llm, tools=full_tool_registry, executor=ToolExecutor(),
                          config=AgentConfig(max_steps=5))

        events = []
        async for event in agent.run("Read /tmp/test.txt"):
            events.append(event)

        tool_call_events = [e for e in events if e.type == AgentEventType.TOOL_CALL]
        tool_result_events = [e for e in events if e.type == AgentEventType.TOOL_RESULT]
        final = [e for e in events if e.type == AgentEventType.FINAL_ANSWER]

        assert len(tool_call_events) >= 1
        assert len(tool_result_events) >= 1
        assert len(final) == 1

    async def test_agent_handles_multiple_tool_calls(self, full_tool_registry):
        """Agent executes multiple tools in sequence (multi-step ReAct)."""
        tool_call_1 = ToolCall(
            id="call_1", type="function",
            function=FunctionCall(name="list_dir", arguments=json.dumps({"path": "."})),
        )
        tool_call_2 = ToolCall(
            id="call_2", type="function",
            function=FunctionCall(name="read_file", arguments=json.dumps({"path": "file.txt"})),
        )
        llm = MockProvider(responses=[
            LLMResponse(tool_calls=[tool_call_1]),
            LLMResponse(tool_calls=[tool_call_2]),
            LLMResponse(content="I listed the directory and read the file."),
        ])
        agent = ReActAgent(llm=llm, tools=full_tool_registry, executor=ToolExecutor(),
                          config=AgentConfig(max_steps=5))

        events = []
        async for event in agent.run("List then read"):
            events.append(event)

        tool_calls = [e for e in events if e.type == AgentEventType.TOOL_CALL]
        assert len(tool_calls) >= 2, f"Expected 2+ tool calls, got {len(tool_calls)}"

    async def test_agent_error_on_tool_not_found(self, full_tool_registry):
        """Agent handles tool-not-found gracefully: tool result has error status."""
        tool_call = ToolCall(
            id="call_1", type="function",
            function=FunctionCall(name="nonexistent_tool", arguments="{}"),
        )
        llm = MockProvider(responses=[
            LLMResponse(tool_calls=[tool_call]),
            LLMResponse(content="I tried but the tool wasn't available."),
        ])
        agent = ReActAgent(llm=llm, tools=full_tool_registry, config=AgentConfig(max_steps=3))

        events = []
        async for event in agent.run("Use bad tool"):
            events.append(event)

        # Tool-not-found returns a TOOL_RESULT with error status, not an ERROR event
        tool_results = [e for e in events if e.type == AgentEventType.TOOL_RESULT]
        assert len(tool_results) >= 1
        result: ToolResult = tool_results[0].data["result"]
        assert result.status == ToolResultStatus.ERROR
        assert "Tool not found" in result.error_message

    async def test_agent_max_steps_exceeded(self, full_tool_registry):
        """Agent stops after exceeding max_steps with fallback final answer."""
        tool_call = ToolCall(
            id="call_stuck", type="function",
            function=FunctionCall(name="read_file", arguments=json.dumps({"path": "loop.txt"})),
        )
        infinite_responses = [LLMResponse(tool_calls=[tool_call])] * 20
        llm = MockProvider(responses=infinite_responses)
        agent = ReActAgent(llm=llm, tools=full_tool_registry, executor=ToolExecutor(),
                          config=AgentConfig(max_steps=3))

        events = []
        async for event in agent.run("Loop"):
            events.append(event)

        final = [e for e in events if e.type == AgentEventType.FINAL_ANSWER]
        assert len(final) >= 1
        content = final[-1].data.get("content", "")
        assert "maximum" in content.lower() or "steps" in content.lower(), \
            f"Expected max steps message, got: {content}"


# ---------------------------------------------------------------------------
# Memory Integration
# ---------------------------------------------------------------------------

class TestMemoryIntegration:
    async def test_agent_saves_memory_via_tool(self, full_tool_registry, memory_manager):
        """Agent saves to memory via memory_save tool call."""
        await memory_manager.initialize()
        register_memory_tools(full_tool_registry, memory_manager)

        tool_call = ToolCall(
            id="call_save", type="function",
            function=FunctionCall(
                name="memory_save",
                arguments=json.dumps({"content": "User's name is Alice"}),
            ),
        )
        llm = MockProvider(responses=[
            LLMResponse(tool_calls=[tool_call]),
            LLMResponse(content="I've remembered that your name is Alice."),
        ])
        agent = ReActAgent(llm=llm, tools=full_tool_registry, executor=ToolExecutor(),
                          config=AgentConfig(max_steps=5))

        events = []
        async for event in agent.run("My name is Alice"):
            events.append(event)

        results = [e for e in events if e.type == AgentEventType.TOOL_RESULT]
        assert len(results) >= 1, f"Expected tool result, got {len(results)} events"

        # Verify memory was actually stored
        recalled = await memory_manager.recall("Alice", user_id="default")
        assert len(recalled) > 0, "Memory should be persisted"
        assert any("Alice" in m.content for m in recalled)

        await memory_manager.close()

    async def test_agent_recalls_memory_via_tool(self, full_tool_registry, memory_manager):
        """Agent recalls memory via memory_recall tool call."""
        await memory_manager.initialize()
        register_memory_tools(full_tool_registry, memory_manager)

        # Pre-save a memory
        await memory_manager.save_conversation(summary="User likes Python programming")

        tool_call = ToolCall(
            id="call_recall", type="function",
            function=FunctionCall(
                name="memory_recall",
                arguments=json.dumps({"query": "Python", "limit": 5}),
            ),
        )
        llm = MockProvider(responses=[
            LLMResponse(tool_calls=[tool_call]),
            LLMResponse(content="I found a memory about you liking Python."),
        ])
        agent = ReActAgent(llm=llm, tools=full_tool_registry, executor=ToolExecutor(),
                          config=AgentConfig(max_steps=5))

        events = []
        async for event in agent.run("What do you remember about me?"):
            events.append(event)

        results = [e for e in events if e.type == AgentEventType.TOOL_RESULT]
        assert len(results) >= 1
        result_obj: ToolResult = results[0].data.get("result")
        assert result_obj.status == ToolResultStatus.SUCCESS, \
            f"Expected success: {result_obj}"

        await memory_manager.close()

    async def test_memory_isolation_between_users(self, memory_manager):
        """Memories for different users are isolated."""
        await memory_manager.initialize()

        # Save for user A
        await memory_manager.save_conversation(user_id="user_a", summary="User A secret")
        # Save for user B
        await memory_manager.save_conversation(user_id="user_b", summary="User B secret")

        # User A can only see their own memories
        a_results = await memory_manager.recall("secret", user_id="user_a")
        assert len(a_results) == 1
        assert "User A" in a_results[0].content

        b_results = await memory_manager.recall("secret", user_id="user_b")
        assert len(b_results) == 1
        assert "User B" in b_results[0].content

        await memory_manager.close()


# ---------------------------------------------------------------------------
# Skills Integration
# ---------------------------------------------------------------------------

class TestSkillsIntegration:
    async def test_skill_triggers_match_user_input(self, sample_skills, full_tool_registry):
        """Skill triggers match user messages containing trigger keywords."""
        from lukawi.skills.executor import match_triggers

        matched = match_triggers("can you code review my project?", sample_skills)
        assert len(matched) >= 1
        assert matched[0].name == "code_review"

    async def test_skill_trigger_no_false_match(self, sample_skills):
        """Non-trigger messages return empty."""
        from lukawi.skills.executor import match_triggers

        matched = match_triggers("hello, how are you?", sample_skills)
        assert matched == []

    async def test_skill_prompt_building(self, sample_skills):
        """Skill prompt contains skill names and descriptions."""
        from lukawi.skills.executor import build_skill_prompt

        prompt = build_skill_prompt(sample_skills)
        assert "code_review" in prompt
        assert "Review code" in prompt

    async def test_skill_injection_format(self, sample_skills):
        """Explicit skill injection contains full instructions."""
        from lukawi.skills.executor import build_skill_injection

        injection = build_skill_injection(sample_skills[0])
        assert "Active Skill: code_review" in injection
        assert "Analyze code" in injection


# ---------------------------------------------------------------------------
# Full Pipeline Integration
# ---------------------------------------------------------------------------

class TestFullPipeline:
    async def test_conversation_with_memory_and_skills(self, full_tool_registry, memory_manager):
        """End-to-end: agent uses memory tools + responds to user context."""
        await memory_manager.initialize()
        register_memory_tools(full_tool_registry, memory_manager)

        # Pre-save context about the user
        await memory_manager.save_conversation(
            user_id="default",
            summary="User is a Python developer working on an AI project.",
        )

        # Step 1: agent recalls memory
        recall_call = ToolCall(
            id="call_r1", type="function",
            function=FunctionCall(name="memory_recall", arguments=json.dumps({"query": "Python developer"})),
        )
        # Step 2: agent gives final answer
        llm = MockProvider(responses=[
            LLMResponse(tool_calls=[recall_call]),
            LLMResponse(content="I see you're a Python developer working on AI. How can I help?"),
        ])
        agent = ReActAgent(llm=llm, tools=full_tool_registry, executor=ToolExecutor(),
                          config=AgentConfig(max_steps=5))

        events = []
        async for event in agent.run("Tell me what you know about me"):
            events.append(event)

        tool_calls = [e for e in events if e.type == AgentEventType.TOOL_CALL]
        final = [e for e in events if e.type == AgentEventType.FINAL_ANSWER]
        assert len(tool_calls) >= 1, "Agent should call memory_recall"
        assert len(final) == 1, "Agent should produce final answer"
        assert "Python" in final[0].data.get("content", "")

        await memory_manager.close()

    async def test_full_tool_registry_has_all_tools(self, full_tool_registry):
        """Verify all builtin tools are registered."""
        tool_names = [t.name for t in full_tool_registry.list_tools()]
        assert "web_fetch" in tool_names
        assert "read_file" in tool_names
        assert "write_file" in tool_names
        assert "edit_file" in tool_names
        assert "list_dir" in tool_names
        assert "exec_command" in tool_names

    async def test_web_fetch_tool_in_agent(self, full_tool_registry):
        """Agent can call web_fetch tool and receive results."""
        tool_call = ToolCall(
            id="call_fetch", type="function",
            function=FunctionCall(name="web_fetch", arguments=json.dumps({"url": "https://example.com"})),
        )
        llm = MockProvider(responses=[
            LLMResponse(tool_calls=[tool_call]),
            LLMResponse(content="I fetched the URL and here's what I found..."),
        ])
        agent = ReActAgent(llm=llm, tools=full_tool_registry, executor=ToolExecutor(),
                          config=AgentConfig(max_steps=5))

        events = []
        async for event in agent.run("Fetch https://example.com"):
            events.append(event)

        tool_results = [e for e in events if e.type == AgentEventType.TOOL_RESULT]
        assert len(tool_results) >= 1

    async def test_agent_preserves_conversation_history(self, full_tool_registry):
        """Agent includes previous messages in history for context."""
        llm = MockProvider(responses=[
            LLMResponse(content="I remember our previous conversation about Python."),
        ])
        agent = ReActAgent(llm=llm, tools=full_tool_registry, config=AgentConfig(max_steps=3))

        history = [
            Message(role=MessageRole.USER, content="I'm learning Python"),
            Message(role=MessageRole.ASSISTANT, content="Python is great! What aspect?"),
        ]

        events = []
        async for event in agent.run("Continue our Python discussion", history=history):
            events.append(event)

        final = [e for e in events if e.type == AgentEventType.FINAL_ANSWER]
        assert len(final) == 1
        # Check that history was passed to the LLM
        assert len(llm.call_history) > 0
        last_messages = llm.call_history[-1]
        # Should contain our history messages + the new one
        assert any("learning Python" in m.content for m in last_messages if m.role == MessageRole.USER)


# ---------------------------------------------------------------------------
# RAG Integration
# ---------------------------------------------------------------------------

class TestRAGIntegration:
    async def test_rag_search_tool_in_agent(self, full_tool_registry):
        """Agent can call rag_search tool and receive results."""
        from lukawi.tools.builtin.rag_search import register_rag_tools

        class FakeRAGManager:
            async def search(self, query, sources=None, limit=5, source_path=None):
                class FakeResult:
                    content = "Lukawi Agent 框架支持 RAG 检索"
                    score = 0.95
                    metadata = {"source_path": "guide.md", "type": "document"}
                return [FakeResult()]
            async def upload_document(self, file_path):
                return {"filename": "test.md", "chunks": 3, "replaced": False}
            async def list_documents(self):
                return []

        register_rag_tools(full_tool_registry, rag_manager=FakeRAGManager())

        tool_call = ToolCall(
            id="call_rag", type="function",
            function=FunctionCall(name="rag_search", arguments=json.dumps({"query": "RAG 框架"})),
        )
        llm = MockProvider(responses=[
            LLMResponse(tool_calls=[tool_call]),
            LLMResponse(content="I found a document about the RAG framework."),
        ])
        agent = ReActAgent(llm=llm, tools=full_tool_registry, executor=ToolExecutor(),
                          config=AgentConfig(max_steps=5))

        events = []
        async for event in agent.run("Search RAG docs"):
            events.append(event)

        tool_results = [e for e in events if e.type == AgentEventType.TOOL_RESULT]
        assert len(tool_results) >= 1
        result: ToolResult = tool_results[0].data["result"]
        assert result.status == ToolResultStatus.SUCCESS, f"Expected SUCCESS, got {result.status}: {result.error_message}"
        assert result.metadata["count"] >= 1

    async def test_rag_search_without_manager_returns_error(self, full_tool_registry):
        """Agent handles rag_search when RAG is not configured."""
        tool_call = ToolCall(
            id="call_rag", type="function",
            function=FunctionCall(name="rag_search", arguments=json.dumps({"query": "test"})),
        )
        llm = MockProvider(responses=[
            LLMResponse(tool_calls=[tool_call]),
            LLMResponse(content="RAG system is not available."),
        ])
        agent = ReActAgent(llm=llm, tools=full_tool_registry, executor=ToolExecutor(),
                          config=AgentConfig(max_steps=5))

        events = []
        async for event in agent.run("Search without RAG"):
            events.append(event)

        tool_results = [e for e in events if e.type == AgentEventType.TOOL_RESULT]
        assert len(tool_results) >= 1
        result: ToolResult = tool_results[0].data["result"]
        assert result.status == ToolResultStatus.ERROR


# ---------------------------------------------------------------------------
# Streaming
# ---------------------------------------------------------------------------

class TestStreaming:
    async def test_mock_provider_streams_word_by_word(self):
        """MockProvider chat_stream yields word-by-word chunks."""
        llm = MockProvider(responses=[
            LLMResponse(content="Hello world from Lukawi"),
        ])
        chunks = []
        async for chunk in llm.chat_stream([]):
            if chunk.content:
                chunks.append(chunk.content)

        assert len(chunks) > 1, f"Expected multiple chunks, got {len(chunks)}"
        full = "".join(chunks)
        assert "Lukawi" in full
