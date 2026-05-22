"""Main TUI application for Lukawi — multi-panel OpenCode-style layout.

Wires together Header, Sidebar, ChatContainer, and StatusBar with
command dispatch via CommandRegistry, theme switching via ThemeRegistry,
and incremental streaming agent output.
"""

from __future__ import annotations

import asyncio
import logging

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Header

from lukawi.agent.core import AgentEventType, ReActAgent
from lukawi.config.models import TUIConfig
from lukawi.llm.base import Message, MessageRole
from lukawi.llm.registry import ModelRegistry
from lukawi.mcp.client import MCPServerConfig
from lukawi.mcp.manager import MCPManager
from lukawi.skills.executor import build_skill_injection, match_triggers
from lukawi.skills.loader import SkillLoader
from lukawi.tui.commands import CommandContext, create_default_registry
from lukawi.tui.events import (
    ChatSubmitted,
    CommandSubmitted,
    SidebarToggle,
    StatusUpdate,
    ThemeChanged,
)
from lukawi.tui.themes import create_default_registry as create_default_theme_registry
from lukawi.tui.widgets.chat import ChatContainer
from lukawi.tui.widgets.sidebar import Sidebar
from lukawi.tui.widgets.status_bar import StatusBar

logger = logging.getLogger(__name__)


class LukawiApp(App):
    """Main Lukawi TUI — multi-panel agent interface."""

    TITLE = "Lukawi Agent"
    SUB_TITLE = "AI Assistant with Tools"

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear", "Clear"),
        Binding("ctrl+m", "models", "Models"),
        Binding("ctrl+b", "toggle_sidebar", "Toggle Sidebar"),
        Binding("ctrl+t", "cycle_theme", "Cycle Theme"),
    ]

    CSS = """
    #main-area {
        height: 1fr;
    }

    #main-area > Sidebar {
        width: 28;
        height: 1fr;
    }

    #main-area > ChatContainer {
        height: 1fr;
        width: 1fr;
    }

    #status-bar {
        height: 1;
        dock: bottom;
    }
    """

    def __init__(
        self,
        agent: ReActAgent,
        model_registry: ModelRegistry | None = None,
        mcp_manager: MCPManager | None = None,
        skill_loader: SkillLoader | None = None,
        mcp_configs: list[MCPServerConfig] | None = None,
        tui_config: TUIConfig | None = None,
    ) -> None:
        super().__init__()
        self.agent = agent
        self.model_registry = model_registry
        self.mcp_manager = mcp_manager
        self.tool_registry = agent.tools
        self.skill_loader = skill_loader
        self.mcp_configs = mcp_configs or []
        self.active_skills: dict[str, str] = {}
        self._processing = False
        self._mcp_connected = False
        self._history: list = []

        self.command_registry = create_default_registry()
        self.theme_registry = create_default_theme_registry()

        if tui_config and tui_config.theme:
            try:
                theme = self.theme_registry.use(tui_config.theme)
                self.theme = theme.name
            except KeyError:
                pass

    def _safe_create_task(self, coro, error_msg: str = "Background task failed") -> asyncio.Task:
        task = asyncio.create_task(coro)
        task.add_done_callback(lambda t: self._log_task_exception(t, error_msg))
        return task

    @staticmethod
    def _log_task_exception(task: asyncio.Task, error_msg: str) -> None:
        if task.exception():
            logger.error(f"{error_msg}: {task.exception()}", exc_info=task.exception())

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-area"):
            yield Sidebar(id="sidebar")
            yield ChatContainer(id="chat-panel")
        yield StatusBar(id="status-bar")

    async def on_mount(self) -> None:
        chat = self.query_one(ChatContainer)
        await chat.add_message(
            "Welcome to Lukawi! Type /help for commands.",
            role="system",
        )

        status_bar = self.query_one(StatusBar)
        status_bar.post_message(
            StatusUpdate(
                model="",
                tokens=0,
                mcp_connected=0,
                mcp_total=len(self.mcp_configs),
                active_skills=0,
            )
        )

        if self.model_registry:
            sidebar = self.query_one(Sidebar)
            models = [m.name for m in self.model_registry.list_models()]
            sidebar.update_models(models)

        chat.focus_input()

        if self.mcp_manager and self.mcp_configs:
            self._safe_create_task(self._connect_mcp(), "MCP connection failed")

    def on_chat_submitted(self, event: ChatSubmitted) -> None:
        if self._processing:
            return
        self._safe_create_task(self._process_message(event.text), "Message processing failed")

    def on_command_submitted(self, event: CommandSubmitted) -> None:
        self._safe_create_task(self._dispatch_command(event.command, event.args), "Command dispatch failed")

    async def _dispatch_command(self, command: str, args: list[str]) -> None:
        try:
            chat = self.query_one(ChatContainer)
            ctx = CommandContext(
                app=self,
                agent=self.agent,
                model_registry=self.model_registry,
                mcp_manager=self.mcp_manager,
                skill_loader=self.skill_loader,
                chat_container=chat,
            )
            result = await self.command_registry.dispatch(command, args, ctx)
            if result:
                await chat.add_message(result, role="system")
        except Exception as e:
            logger.error(f"Command dispatch error: {e}", exc_info=True)
            chat = self.query_one(ChatContainer)
            await chat.add_message(f"\n❌ Command error: {e}", role="system")
        finally:
            self._post_status()

    async def _process_message(self, message: str) -> None:
        self._processing = True
        chat = self.query_one(ChatContainer)
        assistant_msg = None
        tool_msgs: list = []

        try:
            # ── Implicit skill trigger detection ──
            if self.skill_loader:
                all_skills = self.skill_loader.list_skills()
                matched = match_triggers(message, all_skills)
                for skill in matched:
                    if skill.name not in self.active_skills:
                        injection = build_skill_injection(skill)
                        self.active_skills[skill.name] = injection
                        self.agent.inject_system_message(injection)

            await chat.add_message(message, role="user")
            assistant_msg = await chat.add_message("", role="assistant")

            async for event in self.agent.run(message, history=list(self._history)):
                if event.type == AgentEventType.THINKING:
                    assistant_msg.append_token("\n🤔 Thinking...")

                elif event.type == AgentEventType.TOOL_CALL:
                    tool = event.data.get("tool", "unknown")
                    params = event.data.get("params", {})
                    tool_msg = await chat.add_tool_message(tool, params=params, status="running")
                    tool_msgs.append(tool_msg)
                    assistant_msg.append_token(f"\n🔧 Using tool: **{tool}**")

                elif event.type == AgentEventType.TOOL_RESULT:
                    result_data = event.data.get("result")
                    tool_name = event.data.get("tool", "unknown")
                    if result_data and hasattr(result_data, 'status'):
                        status_str = "success" if str(result_data.status) == "success" else "error"
                    else:
                        status_str = "success"
                    if tool_msgs:
                        tool_msgs[-1].update_result(str(result_data), status_str)
                    assistant_msg.append_token(f"\n✅ Tool **{tool_name}** completed")

                elif event.type == AgentEventType.FINAL_ANSWER:
                    content = event.data.get("content", "No response")
                    assistant_msg.append_token(content)

                elif event.type == AgentEventType.ERROR:
                    error = event.data.get("error", "Unknown error")
                    assistant_msg.append_token(f"\n❌ Error: {error}")

                self._post_status()

        except Exception as e:
            logger.error(f"Message processing error: {e}", exc_info=True)
            err_msg = f"\n❌ Error: {e}"
            if assistant_msg:
                assistant_msg.append_token(err_msg)
            else:
                await chat.add_message(err_msg, role="system")

        finally:
            if assistant_msg and assistant_msg.content:
                self._history.append(
                    Message(role=MessageRole.USER, content=message)
                )
                self._history.append(
                    Message(role=MessageRole.ASSISTANT, content=assistant_msg.content)
                )
            self._processing = False
            self._post_status()
            chat.focus_input()

    async def _connect_mcp(self) -> None:
        try:
            if self._mcp_connected or not self.mcp_manager:
                return
            await self.mcp_manager.connect_all(self.mcp_configs)
            await self.mcp_manager.register_tools(self.tool_registry)
            self._mcp_connected = True
        except Exception as e:
            logger.error(f"MCP connection error: {e}", exc_info=True)
        finally:
            self._post_status()

    def _post_status(self) -> None:
        model_name = ""
        if self.model_registry:
            model_name = self.model_registry.current_name or ""

        tokens = 0  # placeholder — future: track token usage
        mcp_connected = self.mcp_manager.connected_count if self.mcp_manager else 0
        mcp_total = len(self.mcp_configs) if self.mcp_configs else 0
        active_skills = len(self.active_skills)

        status_bar = self.query_one(StatusBar)
        status_bar.post_message(
            StatusUpdate(
                model=model_name,
                tokens=tokens,
                mcp_connected=mcp_connected,
                mcp_total=mcp_total,
                active_skills=active_skills,
            )
        )

    def action_clear(self) -> None:
        self.post_message(CommandSubmitted("/clear", []))

    def action_models(self) -> None:
        self.post_message(CommandSubmitted("/models", []))

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one(Sidebar)
        sidebar.collapsed = not sidebar.collapsed
        self.post_message(SidebarToggle(visible=not sidebar.collapsed))

    def action_cycle_theme(self) -> None:
        themes = self.theme_registry.list_themes()
        if not themes:
            return
        current = self.theme_registry.current_name
        idx = themes.index(current) if current in themes else -1
        next_theme = themes[(idx + 1) % len(themes)]
        theme = self.theme_registry.use(next_theme)
        self.theme = theme.name
        self.post_message(ThemeChanged(theme.name))
        self._post_status()


def run_tui(
    config_path: str | None = None,
    model: str | None = None,
    debug: bool = False,
    mock: bool = False,
    mcp_path: str | None = None,
    skills_dir: str | None = None,
) -> None:
    from lukawi.cli import cleanup_context, create_agent_context

    ctx = create_agent_context(
        config_path=config_path,
        model=model,
        debug=debug,
        mock=mock,
        mcp_path=mcp_path,
        skills_dir=skills_dir,
    )

    app = LukawiApp(
        agent=ctx.agent,
        model_registry=ctx.model_registry,
        mcp_manager=ctx.mcp_manager,
        skill_loader=ctx.skill_loader,
        mcp_configs=ctx.mcp_configs,
        tui_config=ctx.config.tui,
    )

    try:
        app.run()
    finally:
        cleanup_context(ctx)
