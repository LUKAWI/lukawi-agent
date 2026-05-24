"""ReAct agent core implementation."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator

from lukawi.config.models import AgentConfig
from lukawi.llm.base import LLMProvider, LLMResponse, Message, MessageRole
from lukawi.tools.base import ToolResult, ToolResultStatus
from lukawi.tools.executor import ToolExecutor
from lukawi.tools.policy import ToolPolicy, PolicyContext
from lukawi.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class AgentEventType(str, Enum):
    THINKING = "thinking"
    STREAMING_TOKEN = "streaming_token"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    FINAL_ANSWER = "final_answer"
    ERROR = "error"
    STEP_COMPLETE = "step_complete"


@dataclass
class AgentEvent:
    type: AgentEventType
    data: dict[str, Any] = field(default_factory=dict)


class StopAgent(Exception):
    pass


class ReActAgent:

    def __init__(
        self,
        llm: LLMProvider,
        tools: ToolRegistry,
        executor: ToolExecutor | None = None,
        config: AgentConfig | None = None,
        memory_manager: Any | None = None,
        policy: ToolPolicy | None = None,
    ):
        self.llm = llm
        self.tools = tools
        self.executor = executor or ToolExecutor()
        self.config = config or AgentConfig()
        self._call_signatures: dict[str, int] = {}
        self._extra_system_messages: list[str] = []
        self.memory_manager = memory_manager
        self.policy = policy

    def inject_system_message(self, content: str) -> None:
        """Add extra content appended after the base system prompt.

        Used by skills and other dynamic context injection.

        Args:
            content: Markdown text to append after the base system prompt
        """
        self._extra_system_messages.append(content)

    def switch_model(self, name: str, provider: LLMProvider) -> None:
        """Switch the LLM provider at runtime.

        Called when the user switches models via the API or TUI.

        Args:
            name: Provider name (for reference)
            provider: The new LLM provider instance
        """
        self.llm = provider

    async def _maybe_index_conversation(self, session_id: str | None = None) -> None:
        """Index current conversation turn into RAG if available."""
        if getattr(self, 'memory_manager', None) and hasattr(self.memory_manager, 'rag') and self.memory_manager.rag:
            try:
                await self.memory_manager.save_conversation(session_id=session_id)
            except Exception as e:
                logger.warning("Failed to index conversation: %s", e)

    async def run(
        self,
        user_message: str,
        history: list[Message] | None = None,
        session_id: str | None = None,
    ) -> AsyncGenerator[AgentEvent, None]:
        messages = list(history or [])
        messages.append(Message(role=MessageRole.USER, content=user_message))

        system_content = self.config.system_prompt
        if self._extra_system_messages:
            system_content += "\n\n" + "\n\n".join(self._extra_system_messages)

        if self.memory_manager is not None:
            memories = await self.memory_manager.recall(query=user_message, limit=5, session_id=session_id)
            if memories:
                memory_lines = ["## 相关记忆"]
                for m in memories:
                    memory_lines.append(f"- {m.content} (created: {m.created_at.strftime('%Y-%m-%d')})")
                system_content += "\n\n" + "\n".join(memory_lines)

        if not messages or messages[0].role != MessageRole.SYSTEM:
            messages.insert(0, Message(role=MessageRole.SYSTEM, content=system_content))

        self._call_signatures.clear()

        for step in range(self.config.max_steps):
            try:
                yield AgentEvent(AgentEventType.THINKING, {"step": step})

                tool_schemas = self.tools.list_tools()
                tools_arg = tool_schemas if tool_schemas else None

                full_content = ""
                final_tool_calls = None
                finish_reason = None
                reasoning = None

                async for chunk in self.llm.chat_stream(
                    messages=messages,
                    tools=tools_arg,
                ):
                    if chunk.content:
                        full_content += chunk.content
                        yield AgentEvent(AgentEventType.STREAMING_TOKEN, {
                            "content": chunk.content,
                        })
                    if chunk.tool_calls is not None:
                        final_tool_calls = chunk.tool_calls
                    if chunk.finish_reason:
                        finish_reason = chunk.finish_reason
                    if chunk.reasoning_content:
                        if reasoning is None:
                            reasoning = ""
                        reasoning += chunk.reasoning_content

                response = LLMResponse(
                    content=full_content.strip() if full_content else None,
                    tool_calls=final_tool_calls if final_tool_calls else None,
                    finish_reason=finish_reason or "stop",
                    reasoning_content=reasoning,
                )

                if not response.tool_calls:
                    yield AgentEvent(AgentEventType.FINAL_ANSWER, {
                        "content": response.content or ""
                    })
                    await self._maybe_index_conversation(session_id)
                    return

                results: list[tuple[Any, ToolResult]] = []
                for tool_call in response.tool_calls:
                    tool_name = tool_call.function.name
                    raw_args = tool_call.function.arguments

                    try:
                        tool_params = json.loads(raw_args)
                    except json.JSONDecodeError:
                        yield AgentEvent(AgentEventType.TOOL_CALL, {
                            "tool": tool_name,
                            "params": {"_raw": raw_args},
                        })
                        result = ToolResult.error(
                            f"Invalid JSON in tool call arguments for '{tool_name}': {raw_args[:500]}"
                        )
                        yield AgentEvent(AgentEventType.TOOL_RESULT, {
                            "tool": tool_name,
                            "result": result,
                        })
                        results.append((tool_call, result))
                        continue

                    yield AgentEvent(AgentEventType.TOOL_CALL, {
                        "tool": tool_name,
                        "params": tool_params,
                    })

                    result = await self._act(tool_name, tool_params)

                    yield AgentEvent(AgentEventType.TOOL_RESULT, {
                        "tool": tool_name,
                        "result": result,
                    })

                    results.append((tool_call, result))

                self._observe(messages, response, results)

                yield AgentEvent(AgentEventType.STEP_COMPLETE, {"step": step})

            except StopAgent as e:
                yield AgentEvent(AgentEventType.ERROR, {"error": str(e)})
                return
            except Exception as e:
                yield AgentEvent(AgentEventType.ERROR, {"error": str(e)})
                return

        yield AgentEvent(AgentEventType.FINAL_ANSWER, {
            "content": (
                "I've reached the maximum number of steps. "
                "Please try again with a simpler request."
            )
        })

    async def _think(self, messages: list[Message]) -> LLMResponse:
        tool_schemas = self.tools.list_tools()
        return await self.llm.chat(
            messages=messages,
            tools=tool_schemas if tool_schemas else None,
        )

    async def _act(self, tool_name: str, tool_params: dict[str, Any]) -> ToolResult:
        if self.policy and not self.policy.is_allowed(tool_name, PolicyContext()):
            return ToolResult.denied(f"Tool '{tool_name}' denied by policy")

        if self.config.loop_detection:
            signature = f"{tool_name}:{json.dumps(tool_params, sort_keys=True)}"
            count = self._call_signatures.get(signature, 0) + 1
            self._call_signatures[signature] = count

            if count > self.config.loop_threshold:
                raise StopAgent(
                    f"Loop detected: {tool_name} called {count} times with same parameters"
                )

        try:
            definition, handler = self.tools.get(tool_name)
        except Exception:
            return ToolResult.error(f"Tool not found: {tool_name}")

        return await self.executor.execute(
            definition=definition,
            handler=handler,
            parameters=tool_params,
        )

    def _observe(
        self,
        messages: list[Message],
        response: LLMResponse,
        results: list[tuple[Any, ToolResult]],
    ) -> None:
        messages.append(Message(
            role=MessageRole.ASSISTANT,
            content=response.content,
            tool_calls=[tc for tc, _ in results],
            reasoning_content=response.reasoning_content,
        ))

        for tool_call, result in results:
            status_value = result.status.value
            tool_result_content: dict[str, Any] = {"status": status_value}
            if result.status == ToolResultStatus.SUCCESS:
                tool_result_content["result"] = result.result
            else:
                tool_result_content["error"] = result.error_message

            messages.append(Message(
                role=MessageRole.TOOL,
                content=json.dumps(tool_result_content, default=str),
                tool_call_id=tool_call.id,
            ))
