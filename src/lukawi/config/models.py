from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field
from typing import Union


class DeepSeekConfig(BaseModel):
    api_key: str = ""
    model: str = "deepseek-v4-flash"
    base_url: str = "https://api.deepseek.com"
    max_tokens: int = 4096
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class MockConfig(BaseModel):
    type: str = "mock"
    responses: list[str] = Field(
        default_factory=lambda: ["I'm a mock response for testing."]
    )


class ModelConfig(BaseModel):
    default: str = "deepseek"
    providers: dict[str, Union[DeepSeekConfig, MockConfig]] = Field(
        default_factory=lambda: {
            "deepseek": DeepSeekConfig(),
            "mock": MockConfig(),
        }
    )


class ToolProfileConfig(BaseModel):
    allowed_tools: list[str] = Field(default_factory=lambda: ["*"])
    denied_tools: list[str] = Field(default_factory=list)


class BuiltinToolConfig(BaseModel):
    timeout: int = 30
    follow_redirects: bool = True
    max_content_length: int = 10485760
    allowed_dirs: list[str] = Field(default_factory=list)
    denied_dirs: list[str] = Field(default_factory=list)
    shell: str = "auto"
    dangerous_patterns: list[str] = Field(default_factory=list)


class ToolPolicyConfig(BaseModel):
    default_profile: str = "default"
    profiles: dict[str, ToolProfileConfig] = Field(
        default_factory=lambda: {
            "default": ToolProfileConfig(),
            "restricted": ToolProfileConfig(
                allowed_tools=["web_fetch", "read_file", "list_dir"],
                denied_tools=["exec_command", "write_file", "edit_file"],
            ),
        }
    )
    builtin: dict[str, BuiltinToolConfig] = Field(default_factory=dict)


class SessionMemoryConfig(BaseModel):
    max_messages: int = 100
    context_window_tokens: int = 4000


class LongTermMemoryConfig(BaseModel):
    enabled: bool = True
    db_path: str = str(Path.home() / ".lukawi" / "memory.db")
    vector_search: bool = False
    max_retrieval: int = 10


class MemoryConfig(BaseModel):
    enabled: bool = True
    session: SessionMemoryConfig = Field(default_factory=SessionMemoryConfig)
    longterm: LongTermMemoryConfig = Field(default_factory=LongTermMemoryConfig)


class AgentConfig(BaseModel):
    max_steps: int = 10
    max_tokens: int = 100000
    loop_detection: bool = True
    loop_threshold: int = 3
    system_prompt: str = (
        "You are Lukawi, a helpful AI assistant based on advanced language models. "
        "You and the user share one workspace, and your job is to collaborate with them until their goal is genuinely handled.\n\n"
        "## General Guidelines\n"
        "You bring a senior engineer's judgment to the work, but you let it arrive through attention rather than premature certainty. "
        "You read the context first, resist easy assumptions, and let the shape of the existing information teach you how to move.\n\n"
        "## Engineering Judgment\n"
        "When the user leaves implementation details open, you choose conservatively and in sympathy with the context already in front of you:\n"
        "- You prefer existing patterns and established local practices over inventing new styles of abstraction.\n"
        "- For structured data, you use structured APIs or parsers instead of ad hoc string manipulation whenever reasonable options exist.\n"
        "- You keep responses closely scoped to the request and surrounding context.\n"
        "- You add an abstraction only when it removes real complexity, reduces meaningful duplication, or clearly matches an established pattern.\n\n"
        "## Tool Usage\n"
        "When you need to use a tool, respond with JSON in this format:\n"
        "{\n"
        '  "thinking": "Your reasoning about what to do",\n'
        '  "action": {\n'
        '    "tool": "tool_name",\n'
        '    "parameters": {\n'
        '      "param1": "value1"\n'
        "    }\n"
        "  }\n"
        "}\n\n"
        "When you have the final answer and no longer need to use tools, respond normally without JSON.\n\n"
        "Available tools will be listed in the system context.\n\n"
        "## Autonomy and Persistence\n"
        "You stay with the work until the task is handled end to end whenever feasible. Do not stop at analysis or half-finished fixes. "
        "You carry the work through implementation, verification, and a clear account of the outcome unless the user explicitly pauses or redirects you.\n\n"
        "## Formatting Rules\n"
        "- You may format with GitHub-flavored Markdown.\n"
        "- You add structure only when the task calls for it. You prefer short paragraphs by default.\n"
        "- Avoid nested bullets unless the user explicitly asks for them. Keep lists flat.\n"
        "- Headers are optional; use them only when they genuinely help. If you do use one, make it short Title Case (1-3 words), wrap it in **...**, and do not add a blank line.\n\n"
        "## Important\n"
        "All your responses must be in Chinese."
    )


class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    rich: bool = True
    file: str = ""


class TUIConfig(BaseModel):
    theme: str = "lukawi-dark"
    show_timestamps: bool = True
    show_tool_details: bool = True
    show_sidebar: bool = False
    max_display_messages: int = 100
    markdown: bool = True


class MCPServerEntry(BaseModel):
    name: str = ""
    command: list[str] = Field(default_factory=list)
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)


class MCPConfig(BaseModel):
    servers: list[MCPServerEntry] = Field(default_factory=list)


class SkillsConfig(BaseModel):
    directory: str = "skills"
    auto_load: bool = True


class DevConfig(BaseModel):
    mock: bool = False
    debug: bool = False
    verbose: bool = False


class AppConfig(BaseModel):
    model: ModelConfig = Field(default_factory=ModelConfig)
    tools: ToolPolicyConfig = Field(default_factory=ToolPolicyConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    tui: TUIConfig = Field(default_factory=TUIConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    skills: SkillsConfig = Field(default_factory=SkillsConfig)
    dev: DevConfig = Field(default_factory=DevConfig)
