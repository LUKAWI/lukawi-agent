"""Tests for ReAct agent core."""

import json
import pytest

from lukawi.agent.core import ReActAgent, AgentConfig, AgentEvent, AgentEventType, StopAgent
from lukawi.llm.base import MessageRole, LLMResponse, ToolCall, FunctionCall
from lukawi.llm.mock import MockProvider
from lukawi.tools.base import ToolDefinition, ToolResult, ToolResultStatus, ToolParameter, ToolParameterType
from lukawi.tools.registry import ToolRegistry


@pytest.fixture
def mock_llm():
    return MockProvider()


@pytest.fixture
def tool_registry():
    registry = ToolRegistry()

    async def echo_handler(text: str) -> ToolResult:
        return ToolResult.success(f"Echo: {text}")

    registry.register(
        ToolDefinition(
            name="echo",
            description="Echo text back",
            parameters=[
                ToolParameter(
                    name="text",
                    type=ToolParameterType.STRING,
                    description="Text to echo",
                    required=True,
                )
            ],
        ),
        echo_handler,
    )

    return registry


@pytest.fixture
def agent(mock_llm, tool_registry):
    return ReActAgent(
        llm=mock_llm,
        tools=tool_registry,
        config=AgentConfig(max_steps=5),
    )


class TestReActAgent:
    @pytest.mark.asyncio
    async def test_simple_response(self, agent):
        """Agent yields thinking then final answer when LLM returns direct response."""
        agent.llm = MockProvider(responses=[
            LLMResponse(content="Hello! How can I help?")
        ])

        events = []
        async for event in agent.run("Hello"):
            events.append(event)

        assert any(e.type == AgentEventType.THINKING for e in events)
        assert any(e.type == AgentEventType.FINAL_ANSWER for e in events)

        final = next(e for e in events if e.type == AgentEventType.FINAL_ANSWER)
        assert final.data["content"] == "Hello! How can I help?"

    @pytest.mark.asyncio
    async def test_tool_call(self, agent):
        """Agent executes tool then returns final answer."""
        tool_call = ToolCall(
            id="call_1",
            type="function",
            function=FunctionCall(
                name="echo",
                arguments=json.dumps({"text": "test"}),
            ),
        )

        agent.llm = MockProvider(responses=[
            LLMResponse(tool_calls=[tool_call]),
            LLMResponse(content="Tool said: Echo: test"),
        ])

        events = []
        async for event in agent.run("Echo test"):
            events.append(event)

        assert any(e.type == AgentEventType.TOOL_CALL for e in events)
        assert any(e.type == AgentEventType.TOOL_RESULT for e in events)
        assert any(e.type == AgentEventType.FINAL_ANSWER for e in events)

    @pytest.mark.asyncio
    async def test_loop_detection(self, agent):
        """Agent stops when same tool+args called beyond threshold."""
        agent.config.loop_threshold = 2

        tool_call = ToolCall(
            id="call_1",
            type="function",
            function=FunctionCall(
                name="echo",
                arguments=json.dumps({"text": "loop"}),
            ),
        )

        agent.llm = MockProvider(responses=[
            LLMResponse(tool_calls=[tool_call]),
            LLMResponse(tool_calls=[tool_call]),
            LLMResponse(tool_calls=[tool_call]),
            LLMResponse(content="Should not reach here"),
        ])

        events = []
        async for event in agent.run("Start loop"):
            events.append(event)

        assert any(e.type == AgentEventType.ERROR for e in events)
        error = next(e for e in events if e.type == AgentEventType.ERROR)
        assert "loop" in error.data["error"].lower()

    @pytest.mark.asyncio
    async def test_max_steps(self, agent):
        """Agent stops after reaching max_steps."""
        agent.config.max_steps = 2

        tool_call = ToolCall(
            id="call_1",
            type="function",
            function=FunctionCall(
                name="echo",
                arguments=json.dumps({"text": "step"}),
            ),
        )

        agent.llm = MockProvider(responses=[
            LLMResponse(tool_calls=[tool_call]),
            LLMResponse(tool_calls=[tool_call]),
            LLMResponse(tool_calls=[tool_call]),
        ])

        events = []
        async for event in agent.run("Many steps"):
            events.append(event)

        final = next(e for e in events if e.type == AgentEventType.FINAL_ANSWER)
        assert "maximum" in final.data["content"].lower()

    @pytest.mark.asyncio
    async def test_step_complete_event(self, agent):
        """Agent emits STEP_COMPLETE after each tool execution round."""
        tool_call = ToolCall(
            id="call_1",
            type="function",
            function=FunctionCall(
                name="echo",
                arguments=json.dumps({"text": "step"}),
            ),
        )

        agent.llm = MockProvider(responses=[
            LLMResponse(tool_calls=[tool_call]),
            LLMResponse(content="Done"),
        ])

        events = []
        async for event in agent.run("Step"):
            events.append(event)

        assert any(e.type == AgentEventType.STEP_COMPLETE for e in events)

    @pytest.mark.asyncio
    async def test_history_preserved(self, agent):
        """Agent preserves conversation history across tool calls."""
        tool_call = ToolCall(
            id="call_1",
            type="function",
            function=FunctionCall(
                name="echo",
                arguments=json.dumps({"text": "hi"}),
            ),
        )

        agent.llm = MockProvider(responses=[
            LLMResponse(tool_calls=[tool_call]),
            LLMResponse(content="Done"),
        ])

        async for _ in agent.run("Say hi"):
            pass

        assert agent.llm.call_count == 2
        first_call_messages = agent.llm.call_history[0]
        assert first_call_messages[0].role == MessageRole.SYSTEM
        assert first_call_messages[1].role == MessageRole.USER

    @pytest.mark.asyncio
    async def test_tool_not_found(self, agent):
        """Agent handles missing tool gracefully."""
        tool_call = ToolCall(
            id="call_1",
            type="function",
            function=FunctionCall(
                name="nonexistent",
                arguments=json.dumps({}),
            ),
        )

        agent.llm = MockProvider(responses=[
            LLMResponse(tool_calls=[tool_call]),
            LLMResponse(content="Handled"),
        ])

        events = []
        async for event in agent.run("Use missing tool"):
            events.append(event)

        result_events = [e for e in events if e.type == AgentEventType.TOOL_RESULT]
        assert len(result_events) > 0
        assert result_events[0].data["result"].status == ToolResultStatus.ERROR

    @pytest.mark.asyncio
    async def test_custom_system_prompt(self, tool_registry):
        """Agent uses custom system prompt from config."""
        custom_prompt = "You are a pirate."
        config = AgentConfig(system_prompt=custom_prompt)
        llm = MockProvider(responses=[LLMResponse(content="Ahoy!")])
        agent = ReActAgent(llm=llm, tools=tool_registry, config=config)

        async for _ in agent.run("Hello"):
            pass

        first_call_messages = llm.call_history[0]
        assert first_call_messages[0].content == custom_prompt

    @pytest.mark.asyncio
    async def test_loop_detection_resets(self, mock_llm, tool_registry):
        """Loop detection resets between runs."""
        config = AgentConfig(max_steps=5, loop_threshold=2)
        agent = ReActAgent(llm=mock_llm, tools=tool_registry, config=config)

        tool_call = ToolCall(
            id="call_1",
            type="function",
            function=FunctionCall(
                name="echo",
                arguments=json.dumps({"text": "test"}),
            ),
        )

        agent.llm = MockProvider(responses=[
            LLMResponse(tool_calls=[tool_call]),
            LLMResponse(content="Done"),
        ])
        events = []
        async for event in agent.run("First"):
            events.append(event)
        assert any(e.type == AgentEventType.FINAL_ANSWER for e in events)
        assert not any(e.type == AgentEventType.ERROR for e in events)

        agent.llm = MockProvider(responses=[
            LLMResponse(tool_calls=[tool_call]),
            LLMResponse(content="Done"),
        ])
        events = []
        async for event in agent.run("Second"):
            events.append(event)
        assert any(e.type == AgentEventType.FINAL_ANSWER for e in events)
        assert not any(e.type == AgentEventType.ERROR for e in events)


class TestAgentEvent:
    def test_event_creation(self):
        event = AgentEvent(type=AgentEventType.THINKING, data={"step": 0})
        assert event.type == AgentEventType.THINKING
        assert event.data == {"step": 0}

    def test_event_default_data(self):
        event = AgentEvent(type=AgentEventType.FINAL_ANSWER)
        assert event.data == {}


class TestAgentConfig:
    def test_defaults(self):
        config = AgentConfig()
        assert config.max_steps == 10
        assert config.loop_detection is True
        assert config.loop_threshold == 3
        assert "JSON" in config.system_prompt or "tool" in config.system_prompt.lower()


class TestAgentReasoningContent:
    @pytest.mark.asyncio
    async def test_reasoning_content_preserved(self, tool_registry):
        """Agent preserves reasoning_content in messages for next LLM call."""
        tool_call = ToolCall(
            id="call_1",
            type="function",
            function=FunctionCall(
                name="echo",
                arguments=json.dumps({"text": "hello"}),
            ),
        )

        llm = MockProvider(responses=[
            LLMResponse(
                content=None,
                reasoning_content="I need to echo the message",
                tool_calls=[tool_call],
                finish_reason="tool_calls",
            ),
            LLMResponse(content="Done!"),
        ])
        agent = ReActAgent(llm=llm, tools=tool_registry, config=AgentConfig(max_steps=5))

        async for _ in agent.run("Echo hello"):
            pass

        assert llm.call_count == 2
        second_call_messages = llm.call_history[1]

        assistant_msgs = [m for m in second_call_messages if m.role == MessageRole.ASSISTANT]
        assert len(assistant_msgs) >= 1

        last_assistant = assistant_msgs[-1]
        assert last_assistant.reasoning_content == "I need to echo the message"
        assert last_assistant.tool_calls is not None
        assert len(last_assistant.tool_calls) == 1
        assert last_assistant.tool_calls[0].function.name == "echo"

    @pytest.mark.asyncio
    async def test_content_and_reasoning_preserved(self, tool_registry):
        """Agent preserves both content and reasoning_content in assistant message."""
        tool_call = ToolCall(
            id="call_1",
            type="function",
            function=FunctionCall(
                name="echo",
                arguments=json.dumps({"text": "test"}),
            ),
        )

        llm = MockProvider(responses=[
            LLMResponse(
                content="Let me use a tool",
                reasoning_content="I'll echo this",
                tool_calls=[tool_call],
                finish_reason="tool_calls",
            ),
            LLMResponse(content="Done!"),
        ])
        agent = ReActAgent(llm=llm, tools=tool_registry, config=AgentConfig(max_steps=5))

        async for _ in agent.run("Echo test"):
            pass

        second_call_messages = llm.call_history[1]
        assistant_msgs = [m for m in second_call_messages if m.role == MessageRole.ASSISTANT]
        last_assistant = assistant_msgs[-1]
        assert last_assistant.content == "Let me use a tool"
        assert last_assistant.reasoning_content == "I'll echo this"
        assert len(last_assistant.tool_calls) == 1


class TestAgentMalformedJson:
    @pytest.mark.asyncio
    async def test_malformed_json_returns_error(self, tool_registry):
        """Agent handles malformed JSON in tool call arguments gracefully."""
        tool_call = ToolCall(
            id="call_1",
            type="function",
            function=FunctionCall(
                name="echo",
                arguments="not valid json {{{",
            ),
        )

        llm = MockProvider(responses=[
            LLMResponse(tool_calls=[tool_call]),
            LLMResponse(content="I see there was an error"),
        ])
        agent = ReActAgent(llm=llm, tools=tool_registry, config=AgentConfig(max_steps=5))

        events = []
        async for event in agent.run("Do something invalid"):
            events.append(event)

        assert any(e.type == AgentEventType.TOOL_RESULT for e in events)
        result_events = [e for e in events if e.type == AgentEventType.TOOL_RESULT]
        assert result_events[0].data["result"].status == ToolResultStatus.ERROR
        assert "Invalid JSON" in result_events[0].data["result"].error_message

    @pytest.mark.asyncio
    async def test_non_serializable_result(self, tool_registry):
        """Agent handles non-serializable tool result without crashing json.dumps."""
        registry = tool_registry

        async def complex_handler() -> ToolResult:
            from datetime import datetime
            return ToolResult.success({
                "timestamp": datetime.now(),
                "tags": {"a", "b"},
                "count": 42,
            })

        registry.register(
            ToolDefinition(
                name="complex",
                description="Returns non-serializable data",
                parameters=[],
            ),
            complex_handler,
        )

        tool_call = ToolCall(
            id="call_1",
            type="function",
            function=FunctionCall(
                name="complex",
                arguments=json.dumps({}),
            ),
        )

        llm = MockProvider(responses=[
            LLMResponse(tool_calls=[tool_call]),
            LLMResponse(content="Processed complex result"),
        ])
        agent = ReActAgent(llm=llm, tools=registry, config=AgentConfig(max_steps=5))

        events = []
        async for event in agent.run("Get complex data"):
            events.append(event)

        result_events = [e for e in events if e.type == AgentEventType.TOOL_RESULT]
        assert len(result_events) > 0
        assert result_events[0].data["result"].status == ToolResultStatus.SUCCESS

        final = next((e for e in events if e.type == AgentEventType.FINAL_ANSWER), None)
        assert final is not None


class TestStopAgent:
    def test_is_exception(self):
        assert issubclass(StopAgent, Exception)


class TestAgentPolicyEnforcement:

    @pytest.mark.asyncio
    async def test_policy_blocks_denied_tool(self, tool_registry):
        """Agent returns DENIED when policy blocks a tool."""
        from lukawi.agent.core import ReActAgent, AgentConfig
        from lukawi.tools.policy import ToolPolicy, PolicyContext
        from lukawi.config.models import ToolPolicyConfig, ToolProfileConfig

        config = ToolPolicyConfig(
            profiles={
                "default": ToolProfileConfig(
                    allowed_tools=["*"],
                    denied_tools=["echo"]
                )
            }
        )
        policy = ToolPolicy(config)
        agent = ReActAgent(
            llm=MockProvider(responses=[
                LLMResponse(tool_calls=[ToolCall(
                    id="call_1", type="function",
                    function=FunctionCall(name="echo", arguments=json.dumps({"text": "test"})),
                )]),
                LLMResponse(content="Tool was denied."),
            ]),
            tools=tool_registry,
            config=AgentConfig(max_steps=5),
            policy=policy,
        )

        events = []
        async for event in agent.run("Run denied tool"):
            events.append(event)

        result_events = [e for e in events if e.type == AgentEventType.TOOL_RESULT]
        assert len(result_events) >= 1
        assert result_events[0].data["result"].status == ToolResultStatus.DENIED

    @pytest.mark.asyncio
    async def test_policy_allows_permitted_tool(self, tool_registry):
        """Agent executes tool normally when policy allows it."""
        from lukawi.agent.core import ReActAgent, AgentConfig
        from lukawi.tools.policy import ToolPolicy, PolicyContext
        from lukawi.config.models import ToolPolicyConfig, ToolProfileConfig

        config = ToolPolicyConfig(
            profiles={
                "default": ToolProfileConfig(
                    allowed_tools=["echo"],
                    denied_tools=[]
                )
            }
        )
        policy = ToolPolicy(config)
        agent = ReActAgent(
            llm=MockProvider(responses=[
                LLMResponse(tool_calls=[ToolCall(
                    id="call_1", type="function",
                    function=FunctionCall(name="echo", arguments=json.dumps({"text": "hello"})),
                )]),
                LLMResponse(content="Tool executed."),
            ]),
            tools=tool_registry,
            config=AgentConfig(max_steps=5),
            policy=policy,
        )

        events = []
        async for event in agent.run("Run allowed tool"):
            events.append(event)

        result_events = [e for e in events if e.type == AgentEventType.TOOL_RESULT]
        assert len(result_events) >= 1
        assert result_events[0].data["result"].status == ToolResultStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_no_policy_allows_all(self, tool_registry):
        """Agent executes tool when no policy is configured."""
        from lukawi.agent.core import ReActAgent, AgentConfig

        agent = ReActAgent(
            llm=MockProvider(responses=[
                LLMResponse(tool_calls=[ToolCall(
                    id="call_1", type="function",
                    function=FunctionCall(name="echo", arguments=json.dumps({"text": "test"})),
                )]),
                LLMResponse(content="Done."),
            ]),
            tools=tool_registry,
            config=AgentConfig(max_steps=5),
        )

        events = []
        async for event in agent.run("Run tool"):
            events.append(event)

        result_events = [e for e in events if e.type == AgentEventType.TOOL_RESULT]
        assert len(result_events) >= 1
        assert result_events[0].data["result"].status == ToolResultStatus.SUCCESS
