"""Shared server state — holds all subsystem references."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from lukawi.agent.core import ReActAgent
from lukawi.config.models import AppConfig, TUIConfig
from lukawi.llm.registry import ModelRegistry
from lukawi.mcp.client import MCPServerConfig
from lukawi.mcp.manager import MCPManager
from lukawi.memory.manager import MemoryManager
from lukawi.skills.loader import SkillLoader
from lukawi.tools.registry import ToolRegistry


@dataclass
class ServerState:
    agent: ReActAgent | None = None
    model_registry: ModelRegistry | None = None
    tool_registry: ToolRegistry | None = None
    mcp_manager: MCPManager | None = None
    skill_loader: SkillLoader | None = None
    mcp_configs: list[MCPServerConfig] = field(default_factory=list)
    config: AppConfig | None = None
    tui_config: TUIConfig | None = None
    active_skills: dict[str, str] = field(default_factory=dict)
    selected_skills: set[str] = field(default_factory=set)
    memory_manager: MemoryManager | None = None
    rag_manager: RAGManager | None = None


if TYPE_CHECKING:
    from lukawi.rag.manager import RAGManager
