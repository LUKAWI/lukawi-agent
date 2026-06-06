from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from lukawi.config.settings import load_config
from lukawi.config.models import AgentConfig, AppConfig, DeepSeekConfig, CustomModelConfig, MockConfig
from lukawi.llm.registry import ModelRegistry
from lukawi.llm.deepseek import DeepSeekProvider
from lukawi.llm.mock import MockProvider
from lukawi.agent.core import ReActAgent
from lukawi.tools.registry import ToolRegistry
from lukawi.tools.executor import ToolExecutor
from lukawi.tools.policy import ToolPolicy
from lukawi.tools.builtin.web_fetch import register_web_fetch
from lukawi.tools.builtin.file_ops import register_file_ops
from lukawi.tools.builtin.shell import register_shell
from lukawi.config.user_config import load_mcp_servers, merge_mcp_configs, save_mcp_servers
from lukawi.utils.logging import setup_logging
from lukawi.mcp.client import MCPServerConfig as MCPClientConfig
from lukawi.mcp.manager import MCPManager
from lukawi.skills.loader import SkillLoader
from lukawi.skills.executor import build_skill_prompt
from lukawi.memory.manager import MemoryManager

if TYPE_CHECKING:
    from lukawi.rag.manager import RAGManager

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    config: AppConfig
    model_registry: ModelRegistry | None
    memory_manager: MemoryManager | None
    tool_registry: ToolRegistry
    mcp_manager: MCPManager
    mcp_configs: list[MCPClientConfig]
    skill_loader: SkillLoader | None
    agent: ReActAgent
    rag_manager: RAGManager | None = None


def _setup_model_registry(config: AppConfig, mock: bool = False) -> ModelRegistry:
    registry = ModelRegistry()
    if mock:
        registry.register("mock", MockProvider())
        registry.use("mock")
        return registry
    for name, provider_config in config.model.providers.items():
        if isinstance(provider_config, DeepSeekConfig):
            if provider_config.api_key:
                registry.register(name, DeepSeekProvider(provider_config))
        elif isinstance(provider_config, CustomModelConfig):
            if provider_config.api_key:
                # Reuse DeepSeekProvider for custom OpenAI-compatible APIs
                registry.register(name, DeepSeekProvider(provider_config))
        elif isinstance(provider_config, MockConfig):
            registry.register(name, MockProvider())
    if config.model.default and registry.has(config.model.default):
        registry.use(config.model.default)
    return registry


def _setup_tool_registry(memory_manager: MemoryManager | None = None) -> ToolRegistry:
    registry = ToolRegistry()
    register_web_fetch(registry)
    register_file_ops(registry)
    register_shell(registry)
    # register_memory_tools(registry, memory_manager)  # temporarily disabled
    return registry


def _build_system_prompt(config: AppConfig, skills_prompt: str = "") -> str:
    prompt = config.agent.system_prompt
    if skills_prompt:
        prompt += "\n\n" + skills_prompt
    return prompt


def create_agent_context(
    config_path: str | None = None,
    model: str | None = None,
    debug: bool = False,
    mock: bool = False,
    mcp_path: str | None = None,
    skills_dir: str | None = None,
) -> AgentContext:
    config = load_config(config_path)

    setup_logging(
        level="DEBUG" if debug else config.logging.level,
        log_file=config.logging.file or None,
        rich=config.logging.rich,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    if model:
        config.model.default = model

    model_registry = _setup_model_registry(config, mock=mock)

    # === RAG initialization ===
    rag_manager = None
    if config.rag.enabled:
        from lukawi.rag.embedder import DashScopeEmbedder, MockEmbedder
        from lukawi.rag.store import VectorStore
        from lukawi.rag.manager import RAGManager

        if config.rag.dashscope.api_key:
            embedder = DashScopeEmbedder(
                api_key=config.rag.dashscope.api_key,
                model=config.rag.dashscope.model,
                dimensions=config.rag.dashscope.dimensions,
            )
            logger.info("RAG using DashScope embedder")
        else:
            embedder = MockEmbedder()
            logger.info("RAG using MockEmbedder (no DASHSCOPE_API_KEY set, %d dims)", embedder.dimensions)

        store = VectorStore(persist_dir=config.rag.chroma_db_dir, embedder=embedder)
        rag_manager = RAGManager(
            embedder=embedder,
            store=store,
            chunk_size=config.rag.chunk_size,
            chunk_overlap=config.rag.chunk_overlap,
        )
        asyncio.run(rag_manager.initialize())
        logger.info("RAG initialized with ChromaDB at %s", config.rag.chroma_db_dir)

    memory_manager = None
    if config.memory.enabled:
        memory_manager = MemoryManager(
            db_path=config.memory.longterm.db_path,
            session_max_messages=config.memory.session.max_messages,
            longterm_enabled=config.memory.longterm.enabled,
            rag_manager=rag_manager,
        )
        asyncio.run(memory_manager.initialize())

    tool_registry = _setup_tool_registry(memory_manager=memory_manager)

    # RAG tools
    from lukawi.tools.builtin.rag_search import register_rag_tools
    register_rag_tools(tool_registry, rag_manager)

    mcp_manager = MCPManager()
    project_configs = [
        MCPClientConfig(name=s.name, command=s.command, args=s.args, env=s.env)
        for s in config.mcp.servers
    ]
    user_configs = load_mcp_servers()
    all_configs = merge_mcp_configs(project_configs, user_configs)
    save_mcp_servers(all_configs)

    skills_prompt = ""
    skill_loader = None
    skills_dir_path = skills_dir or config.skills.directory
    if config.skills.auto_load and skills_dir_path:
        skill_loader = SkillLoader(skills_dir_path)
        loaded_skills = skill_loader.load_directory()
        if loaded_skills:
            skills_prompt = build_skill_prompt(loaded_skills)

    agent_config = AgentConfig(
        max_steps=config.agent.max_steps,
        max_tokens=config.agent.max_tokens,
        loop_detection=config.agent.loop_detection,
        loop_threshold=config.agent.loop_threshold,
        system_prompt=_build_system_prompt(config, skills_prompt),
    )

    agent = ReActAgent(
        llm=model_registry.current if model_registry else None,
        tools=tool_registry,
        executor=ToolExecutor(),
        config=agent_config,
        memory_manager=memory_manager,
        policy=ToolPolicy(config.tools),
    )

    # MCP connection deferred to caller (webui: FastAPI startup, repl: on connect)

    return AgentContext(
        config=config,
        model_registry=model_registry,
        memory_manager=memory_manager,
        tool_registry=tool_registry,
        mcp_manager=mcp_manager,
        mcp_configs=all_configs,
        skill_loader=skill_loader,
        agent=agent,
        rag_manager=rag_manager,
    )


def cleanup_context(ctx: AgentContext) -> None:
    if ctx.memory_manager:
        asyncio.run(ctx.memory_manager.close())
    if ctx.rag_manager:
        asyncio.run(ctx.rag_manager.close())
    if ctx.mcp_manager.connected_count > 0:
        try:
            asyncio.run(ctx.mcp_manager.disconnect_all())
        except Exception:
            pass
