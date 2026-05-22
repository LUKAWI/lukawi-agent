# Lukawi Agent Framework - 开发规范文档

## 文档版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-05-13 | Lukawi Team | 初始版本 |

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术栈与依赖](#2-技术栈与依赖)
3. [架构设计](#3-架构设计)
4. [模块规范](#4-模块规范)
5. [API 接口规范](#5-api-接口规范)
6. [数据模型规范](#6-数据模型规范)
7. [测试规范](#7-测试规范)
8. [代码风格规范](#8-代码风格规范)
9. [提交规范](#9-提交规范)
10. [开发检查清单](#10-开发检查清单)

---

## 1. 项目概述

### 1.1 项目目标

构建一个轻量级 AI Agent 框架，具备以下核心能力：

- ✅ 接收用户自然语言指令
- ✅ 自主选择合适工具
- ✅ 调用工具并获取结果
- ✅ 整理结果后回复用户
- ✅ 支持多轮"思考-行动"循环（ReAct 模式）

### 1.2 硬性约束

| 约束类型 | 具体要求 | 验证方式 |
|----------|----------|----------|
| **平台适配** | 首要适配 Windows 系统 | 所有测试在 Windows 通过 |
| **路径处理** | 使用 pathlib，避免硬编码 Unix 路径 | 代码审查 |
| **编码** | UTF-8 优先 | 测试非 ASCII 路径 |
| **框架限制** | 禁止直接复用 OpenClaw、LangChain | 依赖审计 |
| **可复用组件** | web_fetch、本地记忆系统 | 模块化设计 |

### 1.3 项目结构

```
lukawi-agent/
├── CLAUDE.md                    # 项目理解与规范
├── DEVELOPMENT_SPEC.md          # 本文档 - 开发规范
├── README.md                    # 用户文档
├── pyproject.toml               # 项目配置
├── .gitignore                   # Git 忽略规则
├── config/
│   └── default.yaml             # 默认配置
├── src/
│   └── lukawi/
│       ├── __init__.py
│       ├── main.py              # 入口点
│       ├── agent/               # Agent 核心引擎
│       ├── llm/                 # LLM 抽象层
│       ├── tools/               # 工具管理系统
│       ├── memory/              # 记忆系统
│       ├── mcp/                 # MCP 接口
│       ├── skills/              # Agent Skills 系统
│       ├── tui/                 # 终端界面
│       ├── config/              # 配置管理
│       └── utils/               # 工具函数
├── tests/                       # 测试目录
│   ├── conftest.py
│   ├── test_agent/
│   ├── test_llm/
│   ├── test_tools/
│   ├── test_memory/
│   ├── test_tui/
│   └── test_integration/
└── skills/                      # 内置技能文件
    └── web_search/
        └── SKILL.md
```

---

## 2. 技术栈与依赖

### 2.1 核心依赖

| 包名 | 版本 | 用途 | 必需 |
|------|------|------|------|
| `textual` | >=0.40.0 | TUI 框架 | ✅ |
| `rich` | >=13.0.0 | 终端富文本渲染 | ✅ |
| `httpx` | >=0.25.0 | HTTP 客户端 | ✅ |
| `openai` | >=1.0.0 | DeepSeek API 客户端 | ✅ |
| `pydantic` | >=2.0.0 | 数据验证和配置模型 | ✅ |
| `pyyaml` | >=6.0 | YAML 配置解析 | ✅ |
| `python-dotenv` | >=1.0.0 | 环境变量加载 | ✅ |
| `aiosqlite` | >=0.19.0 | 异步 SQLite | ✅ |
| `numpy` | >=1.24.0 | 向量运算 | ✅ |

### 2.2 开发依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| `pytest` | >=7.0.0 | 测试框架 |
| `pytest-asyncio` | >=0.21.0 | 异步测试支持 |
| `respx` | >=0.21.0 | HTTP mocking |
| `ruff` | >=0.1.0 | 代码检查和格式化 |
| `mypy` | >=1.0.0 | 静态类型检查 |

### 2.3 Python 版本

- **最低版本**: Python 3.10
- **推荐版本**: Python 3.11 或 3.12
- **不支持**: Python 3.9 及以下

---

## 3. 架构设计

### 3.1 核心架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        TUI Layer (Textual)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Chat Widget │  │ Input Widget│  │ Command Parser          │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Core (ReAct Loop)                    │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Think → Act → Observe → Repeat                            ││
│  │  • Budget controls (max steps, token limit)                ││
│  │  • Loop detection (same tool+args signature)               ││
│  │  • Graceful stop conditions                                ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────────────────┐
│   LLM Layer   │  │  Tool System  │  │     Memory System         │
│  ┌───────────┐│  │  ┌───────────┐│  │  ┌───────────────────────┐│
│  │ DeepSeek  ││  │  │ Registry  ││  │  │ Session Memory        ││
│  │ Provider  ││  │  │ Policy    ││  │  │ (In-Memory)           ││
│  │ Mock      ││  │  │ Executor  ││  │  ├───────────────────────┤│
│  │ Provider  ││  │  │ Hooks     ││  │  │ Working Memory        ││
│  └───────────┘│  │  └───────────┘│  │  │ (SQLite)              ││
│  ┌───────────┐│  │  ┌───────────┐│  │  ├───────────────────────┤│
│  │ Registry  ││  │  │ Builtins: ││  │  │ Long-Term Memory      ││
│  │ (switch)  ││  │  │ •web_fetch││  │  │ (SQLite + Vectors)    ││
│  └───────────┘│  │  │ •file_ops ││  │  └───────────────────────┘│
└───────────────┘  │  │ •shell    ││  └───────────────────────────┘
                   │  └───────────┘│
                   └───────────────┘
```

### 3.2 设计模式

| 模式 | 来源 | 应用位置 | 说明 |
|------|------|----------|------|
| **ExecutionEnv** | Pi Agent | `tools/base.py` | 文件系统和进程抽象接口 |
| **Tool Policy Pipeline** | OpenClaw | `tools/policy.py` | 3 层过滤：deny > allow > profile |
| **Hook System** | DeepSeek-TUI | `tools/executor.py` | 工具执行前后钩子 |
| **ReAct Loop** | 学术论文 | `agent/core.py` | 思考-行动-观察循环 |
| **Provider Pattern** | OpenCode | `llm/` | LLM 提供者抽象 |

### 3.3 数据流

```
用户输入
    │
    ▼
TUI 接收
    │
    ▼
Agent Core (ReAct Loop)
    │
    ├──→ Think: 构建 prompt，调用 LLM
    │         │
    │         ▼
    │    LLM 返回 JSON:
    │    {
    │      "thinking": "...",
    │      "action": { "tool": "...", "parameters": {...} }
    │    }
    │
    ├──→ Act: 解析 action，查找工具，执行
    │         │
    │         ▼
    │    Tool Executor (with hooks)
    │         │
    │         ▼
    │    Tool Result: { "status": "success", "result": {...} }
    │
    └──→ Observe: 将结果加入历史，判断是否继续
              │
              ▼
         循环 or 返回最终答案
              │
              ▼
         TUI 显示结果
```

---

## 4. 模块规范

### 4.1 Agent 模块 (`src/lukawi/agent/`)

#### 4.1.1 `core.py` - ReAct 循环

**职责**: 实现核心的思考-行动-观察循环

**类设计**:
```python
class ReActAgent:
    """ReAct 模式的 Agent 核心"""
    
    def __init__(
        self,
        llm: LLMProvider,
        tools: ToolRegistry,
        memory: MemoryManager,
        policy: ToolPolicy,
        config: AgentConfig
    ):
        ...
    
    async def run(
        self,
        user_message: str,
        session_id: str,
        user_id: str = "default"
    ) -> AsyncGenerator[AgentEvent, None]:
        """运行 Agent，返回事件流"""
        ...
    
    async def _think(self, history: list[Message]) -> LLMResponse:
        """思考阶段：构建 prompt，调用 LLM"""
        ...
    
    async def _act(self, action: Action) -> ToolResult:
        """行动阶段：执行工具"""
        ...
    
    async def _observe(self, result: ToolResult) -> None:
        """观察阶段：更新历史，检查停止条件"""
        ...
```

**必需功能**:
- [ ] ReAct 循环实现
- [ ] 预算控制（最大步数、token 限制）
- [ ] 循环检测（相同工具+参数签名）
- [ ] 优雅停止条件
- [ ] 事件流返回（支持流式显示）

**事件类型**:
```python
class AgentEvent(Enum):
    THINKING = "thinking"          # Agent 正在思考
    TOOL_CALL = "tool_call"        # 即将调用工具
    TOOL_RESULT = "tool_result"    # 工具返回结果
    FINAL_ANSWER = "final_answer"  # 最终答案
    ERROR = "error"                # 错误
    STEP_COMPLETE = "step_complete" # 一步完成
```

#### 4.1.2 `executor.py` - 工具网关

**职责**: 工具执行的网关，集成策略和钩子

**类设计**:
```python
class ToolGateway:
    """工具执行网关"""
    
    def __init__(
        self,
        registry: ToolRegistry,
        policy: ToolPolicy,
        hooks: ToolHooks
    ):
        ...
    
    async def execute(
        self,
        tool_name: str,
        parameters: dict,
        context: ExecutionContext
    ) -> ToolResult:
        """执行工具，应用策略和钩子"""
        ...
```

**必需功能**:
- [ ] 工具查找和验证
- [ ] 策略过滤（deny > allow > profile）
- [ ] 前置钩子执行（可阻止执行）
- [ ] 后置钩子执行（日志、诊断）
- [ ] 错误处理和超时
- [ ] 调用计数和预算追踪

#### 4.1.3 `planner.py` - 任务规划（可选）

**职责**: 复杂任务的分解和规划

**状态**: Phase 4 可选实现

---

### 4.2 LLM 模块 (`src/lukawi/llm/`)

#### 4.2.1 `base.py` - LLM 提供者接口

**职责**: 定义 LLM 提供者的抽象接口

**类设计**:
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

@dataclass
class Message:
    role: MessageRole
    content: str
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] | None = None

@dataclass
class ToolCall:
    id: str
    type: str  # "function"
    function: FunctionCall

@dataclass
class FunctionCall:
    name: str
    arguments: str  # JSON string

@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list[ToolCall] | None
    usage: TokenUsage
    finish_reason: str

@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class LLMProvider(ABC):
    """LLM 提供者抽象基类"""
    
    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None
    ) -> LLMResponse:
        """发送聊天请求"""
        ...
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None
    ) -> AsyncGenerator[LLMChunk, None]:
        """流式聊天请求"""
        ...
    
    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """获取模型信息"""
        ...
```

**必需功能**:
- [ ] 抽象基类定义
- [ ] 消息类型（支持 tool_calls）
- [ ] 流式响应支持
- [ ] Token 使用统计

#### 4.2.2 `deepseek.py` - DeepSeek 实现

**职责**: DeepSeek API 的具体实现

**类设计**:
```python
class DeepSeekProvider(LLMProvider):
    """DeepSeek API 提供者"""
    
    def __init__(self, config: DeepSeekConfig):
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url="https://api.deepseek.com"
        )
        self.model = config.model
    
    async def chat(self, messages, tools=None, ...) -> LLMResponse:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[m.to_dict() for m in messages],
            tools=[t.to_openai_schema() for t in tools] if tools else None,
            ...
        )
        return LLMResponse.from_openai(response)
```

**必需功能**:
- [ ] OpenAI SDK 兼容调用
- [ ] 工具调用支持（function calling）
- [ ] 流式响应实现
- [ ] 错误处理和重试
- [ ] Token 计数

#### 4.2.3 `mock.py` - Mock 提供者

**职责**: 开发测试用的 Mock 提供者

**类设计**:
```python
class MockProvider(LLMProvider):
    """Mock LLM 提供者，用于开发测试"""
    
    def __init__(self, responses: list[LLMResponse] | None = None):
        self.responses = responses or []
        self.call_count = 0
    
    async def chat(self, messages, tools=None, ...) -> LLMResponse:
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
        else:
            response = self._generate_default_response(messages)
        self.call_count += 1
        return response
```

**必需功能**:
- [ ] 预设响应序列
- [ ] 默认响应生成
- [ ] 调用记录和验证
- [ ] 可配置延迟

#### 4.2.4 `registry.py` - 模型注册表

**职责**: 管理多个 LLM 提供者，支持运行时切换

**类设计**:
```python
class ModelRegistry:
    """模型注册表"""
    
    def __init__(self):
        self._providers: dict[str, LLMProvider] = {}
        self._current: str | None = None
    
    def register(self, name: str, provider: LLMProvider) -> None:
        """注册提供者"""
        ...
    
    def use(self, name: str) -> None:
        """切换当前提供者"""
        ...
    
    @property
    def current(self) -> LLMProvider:
        """获取当前提供者"""
        ...
    
    def list_models(self) -> list[ModelInfo]:
        """列出所有可用模型"""
        ...
```

**必需功能**:
- [ ] 提供者注册
- [ ] 运行时切换
- [ ] 当前提供者获取
- [ ] 模型列表查询

---

### 4.3 工具模块 (`src/lukawi/tools/`)

#### 4.3.1 `base.py` - 工具抽象

**职责**: 定义工具的基础类型和接口

**类型定义**:
```python
from pydantic import BaseModel, Field
from typing import Any, Callable, Awaitable
from enum import Enum

class ToolParameterType(Enum):
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"

class ToolParameter(BaseModel):
    """工具参数定义"""
    name: str
    type: ToolParameterType
    description: str
    required: bool = True
    default: Any = None
    enum: list[Any] | None = None

class ToolDefinition(BaseModel):
    """工具定义"""
    name: str
    description: str
    parameters: list[ToolParameter]
    category: str = "general"
    tags: list[str] = []
    
    def to_openai_schema(self) -> dict:
        """转换为 OpenAI function calling 格式"""
        ...

class ToolResultStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    DENIED = "denied"

class ToolResult(BaseModel):
    """工具执行结果"""
    status: ToolResultStatus
    result: Any = None
    error: str | None = None
    metadata: dict = {}
    
    @classmethod
    def success(cls, result: Any, **kwargs) -> "ToolResult":
        return cls(status=ToolResultStatus.SUCCESS, result=result, **kwargs)
    
    @classmethod
    def error(cls, error: str, **kwargs) -> "ToolResult":
        return cls(status=ToolResultStatus.ERROR, error=error, **kwargs)

# 工具处理函数类型
ToolHandler = Callable[..., Awaitable[ToolResult]]
```

**必需功能**:
- [ ] ToolParameter 定义（支持所有 JSON Schema 类型）
- [ ] ToolDefinition 定义
- [ ] OpenAI Schema 转换
- [ ] ToolResult 状态管理
- [ ] 工具处理函数类型

#### 4.3.2 `registry.py` - 工具注册表

**职责**: 管理工具的注册和发现

**类设计**:
```python
class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, ToolHandler] = {}
    
    def register(
        self,
        definition: ToolDefinition,
        handler: ToolHandler
    ) -> None:
        """注册工具"""
        ...
    
    def register_decorator(self, definition: ToolDefinition):
        """装饰器注册"""
        def decorator(handler: ToolHandler):
            self.register(definition, handler)
            return handler
        return decorator
    
    def get(self, name: str) -> tuple[ToolDefinition, ToolHandler] | None:
        """获取工具"""
        ...
    
    def list_tools(self) -> list[ToolDefinition]:
        """列出所有工具"""
        ...
    
    def has(self, name: str) -> bool:
        """检查工具是否存在"""
        ...
    
    def to_openai_schema(self) -> list[dict]:
        """生成 OpenAI tools 格式"""
        ...
```

**必需功能**:
- [ ] 工具注册（直接和装饰器）
- [ ] 工具查找
- [ ] 工具列表
- [ ] OpenAI Schema 生成
- [ ] 线程安全

#### 4.3.3 `policy.py` - 工具策略

**职责**: 多阶段工具过滤

**类设计**:
```python
class ToolPolicy:
    """工具策略管道"""
    
    def __init__(self, config: ToolPolicyConfig):
        self.config = config
    
    def filter_tools(
        self,
        tools: list[ToolDefinition],
        context: PolicyContext
    ) -> list[ToolDefinition]:
        """过滤工具列表"""
        tools = self._apply_deny_list(tools)
        tools = self._apply_allow_list(tools)
        tools = self._apply_profile_filter(tools, context.profile)
        return tools
    
    def is_allowed(
        self,
        tool_name: str,
        context: PolicyContext
    ) -> bool:
        """检查工具是否允许执行"""
        ...

@dataclass
class PolicyContext:
    profile: str = "default"
    user_id: str = "default"
    session_id: str = ""
```

**策略优先级**:
1. **Deny List**: 拒绝列表（最高优先级）
2. **Allow List**: 允许列表（如果配置了，只允许列表中的工具）
3. **Profile Filter**: 配置文件过滤

**必需功能**:
- [ ] 3 层过滤实现
- [ ] 通配符支持（如 `mcp:*`）
- [ ] Profile 管理
- [ ] 上下文感知

#### 4.3.4 `executor.py` - 工具执行器

**职责**: 执行工具并管理钩子

**类设计**:
```python
class ToolHooks:
    """工具钩子管理器"""
    
    def __init__(self):
        self._pre_hooks: list[PreHook] = []
        self._post_hooks: list[PostHook] = []
    
    def add_pre_hook(self, hook: PreHook) -> None:
        """添加前置钩子"""
        ...
    
    def add_post_hook(self, hook: PostHook) -> None:
        """添加后置钩子"""
        ...
    
    async def run_pre_hooks(
        self,
        tool: ToolDefinition,
        params: dict
    ) -> HookDecision:
        """运行前置钩子"""
        ...
    
    async def run_post_hooks(
        self,
        tool: ToolDefinition,
        params: dict,
        result: ToolResult
    ) -> None:
        """运行后置钩子"""
        ...

@dataclass
class HookDecision:
    allow: bool = True
    modified_params: dict | None = None
    reason: str = ""

# 钩子类型
PreHook = Callable[[ToolDefinition, dict], Awaitable[HookDecision]]
PostHook = Callable[[ToolDefinition, dict, ToolResult], Awaitable[None]]

class ToolExecutor:
    """工具执行器"""
    
    def __init__(self, hooks: ToolHooks | None = None):
        self.hooks = hooks or ToolHooks()
    
    async def execute(
        self,
        definition: ToolDefinition,
        handler: ToolHandler,
        parameters: dict,
        timeout: float = 30.0
    ) -> ToolResult:
        """执行工具"""
        # 运行前置钩子
        decision = await self.hooks.run_pre_hooks(definition, parameters)
        if not decision.allow:
            return ToolResult.error(f"Denied: {decision.reason}")
        
        # 使用修改后的参数
        params = decision.modified_params or parameters
        
        try:
            # 执行工具（带超时）
            result = await asyncio.wait_for(
                handler(**params),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            return ToolResult.error("Tool execution timeout")
        except Exception as e:
            return ToolResult.error(str(e))
        
        # 运行后置钩子
        await self.hooks.run_post_hooks(definition, params, result)
        
        return result
```

**必需功能**:
- [ ] 前置钩子（可阻止执行、修改参数）
- [ ] 后置钩子（日志、诊断）
- [ ] 超时控制
- [ ] 错误处理
- [ ] 钩子决策记录

#### 4.3.5 内置工具

##### `web_fetch.py` - HTTP 请求工具

**工具定义**:
```python
WEB_FETCH_TOOL = ToolDefinition(
    name="web_fetch",
    description="Fetch content from a URL. Returns markdown or text.",
    parameters=[
        ToolParameter(name="url", type="string", description="URL to fetch", required=True),
        ToolParameter(name="format", type="string", description="Output format: markdown, text, html", default="markdown"),
        ToolParameter(name="timeout", type="number", description="Timeout in seconds", default=30),
    ],
    category="web",
    tags=["http", "fetch", "web"]
)
```

**必需功能**:
- [ ] GET/POST 请求支持
- [ ] 响应格式转换（HTML → Markdown）
- [ ] 超时处理
- [ ] 错误处理（网络错误、HTTP 错误）
- [ ] 重定向处理
- [ ] 编码检测

##### `file_ops.py` - 文件操作工具

**工具定义**:
```python
READ_FILE_TOOL = ToolDefinition(
    name="read_file",
    description="Read content from a file",
    parameters=[
        ToolParameter(name="path", type="string", description="File path", required=True),
        ToolParameter(name="encoding", type="string", description="File encoding", default="utf-8"),
    ],
    category="filesystem"
)

WRITE_FILE_TOOL = ToolDefinition(
    name="write_file",
    description="Write content to a file",
    parameters=[
        ToolParameter(name="path", type="string", description="File path", required=True),
        ToolParameter(name="content", type="string", description="Content to write", required=True),
        ToolParameter(name="encoding", type="string", description="File encoding", default="utf-8"),
    ],
    category="filesystem"
)

EDIT_FILE_TOOL = ToolDefinition(
    name="edit_file",
    description="Edit a file by replacing text",
    parameters=[
        ToolParameter(name="path", type="string", description="File path", required=True),
        ToolParameter(name="old_text", type="string", description="Text to replace", required=True),
        ToolParameter(name="new_text", type="string", description="Replacement text", required=True),
    ],
    category="filesystem"
)

LIST_DIR_TOOL = ToolDefinition(
    name="list_dir",
    description="List directory contents",
    parameters=[
        ToolParameter(name="path", type="string", description="Directory path", required=True),
        ToolParameter(name="recursive", type="boolean", description="Recursive listing", default=False),
    ],
    category="filesystem"
)
```

**必需功能**:
- [ ] 文件读取（支持编码指定）
- [ ] 文件写入（创建父目录）
- [ ] 文件编辑（文本替换）
- [ ] 目录列表（递归选项）
- [ ] 路径安全验证（防止路径遍历）
- [ ] Windows 路径兼容

##### `shell.py` - Shell 执行工具

**工具定义**:
```python
EXEC_COMMAND_TOOL = ToolDefinition(
    name="exec_command",
    description="Execute a shell command",
    parameters=[
        ToolParameter(name="command", type="string", description="Command to execute", required=True),
        ToolParameter(name="cwd", type="string", description="Working directory", default=None),
        ToolParameter(name="timeout", type="number", description="Timeout in seconds", default=30),
    ],
    category="system"
)
```

**必需功能**:
- [ ] 命令执行（subprocess）
- [ ] 工作目录支持
- [ ] 超时控制
- [ ] 输出捕获（stdout + stderr）
- [ ] 退出码返回
- [ ] Windows cmd/PowerShell 兼容
- [ ] 危险命令检测（可选钩子）

---

### 4.4 记忆模块 (`src/lukawi/memory/`)

#### 4.4.1 `session.py` - 会话记忆

**职责**: 管理单次会话的对话历史

**类设计**:
```python
class SessionMemory:
    """会话记忆（内存存储）"""
    
    def __init__(self, max_messages: int = 100):
        self._messages: list[Message] = []
        self._max_messages = max_messages
    
    def add(self, message: Message) -> None:
        """添加消息"""
        ...
    
    def get_history(self, limit: int | None = None) -> list[Message]:
        """获取历史消息"""
        ...
    
    def get_context_window(self, max_tokens: int = 4000) -> list[Message]:
        """获取上下文窗口（token 限制）"""
        ...
    
    def clear(self) -> None:
        """清空会话"""
        ...
    
    @property
    def message_count(self) -> int:
        """消息数量"""
        ...
```

**必需功能**:
- [ ] 消息添加和获取
- [ ] 上下文窗口管理（token 限制）
- [ ] 会话清空
- [ ] 消息计数

#### 4.4.2 `longterm.py` - 长期记忆

**职责**: 持久化存储长期记忆

**类设计**:
```python
class LongTermMemory:
    """长期记忆（SQLite 存储）"""
    
    def __init__(self, db_path: str = "memory.db"):
        self.db_path = db_path
    
    async def initialize(self) -> None:
        """初始化数据库"""
        ...
    
    async def add(
        self,
        content: str,
        metadata: dict,
        user_id: str,
        agent_id: str = "lukawi"
    ) -> str:
        """添加记忆"""
        ...
    
    async def search(
        self,
        query: str,
        user_id: str,
        limit: int = 10
    ) -> list[Memory]:
        """搜索记忆"""
        ...
    
    async def get_all(
        self,
        user_id: str,
        limit: int = 100
    ) -> list[Memory]:
        """获取所有记忆"""
        ...
    
    async def update(self, memory_id: str, content: str) -> None:
        """更新记忆"""
        ...
    
    async def delete(self, memory_id: str) -> None:
        """删除记忆"""
        ...

@dataclass
class Memory:
    id: str
    content: str
    metadata: dict
    user_id: str
    agent_id: str
    created_at: datetime
    updated_at: datetime
```

**存储结构**:
```sql
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSON,
    user_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    embedding BLOB,  -- 可选：向量嵌入
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_id ON memories(user_id);
CREATE INDEX idx_agent_id ON memories(agent_id);
```

**必需功能**:
- [ ] SQLite 异步操作
- [ ] 记忆 CRUD
- [ ] 用户/Agent 隔离
- [ ] 基础搜索（关键词匹配）
- [ ] 向量搜索（可选，Phase 5+）

#### 4.4.3 `manager.py` - 记忆管理器

**职责**: 统一管理会话和长期记忆

**类设计**:
```python
class MemoryManager:
    """记忆管理器"""
    
    def __init__(self, config: MemoryConfig):
        self.session = SessionMemory()
        self.longterm = LongTermMemory(config.db_path)
        self.config = config
    
    async def initialize(self) -> None:
        """初始化长期记忆"""
        await self.longterm.initialize()
    
    def add_message(self, message: Message) -> None:
        """添加消息到会话记忆"""
        self.session.add(message)
    
    async def save_conversation(
        self,
        user_id: str,
        session_id: str
    ) -> None:
        """保存会话到长期记忆"""
        ...
    
    async def recall(
        self,
        query: str,
        user_id: str,
        limit: int = 5
    ) -> list[Memory]:
        """从长期记忆召回"""
        ...
    
    def get_context(self, max_tokens: int = 4000) -> list[Message]:
        """获取当前上下文"""
        return self.session.get_context_window(max_tokens)
```

**必需功能**:
- [ ] 会话和长期记忆统一接口
- [ ] 会话保存到长期记忆
- [ ] 记忆召回
- [ ] 上下文获取
- [ ] 用户/会话隔离

---

### 4.5 TUI 模块 (`src/lukawi/tui/`)

#### 4.5.1 `app.py` - 主应用

**职责**: Textual 应用主框架

**类设计**:
```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.binding import Binding

class LukawiApp(App):
    """Lukawi TUI 应用"""
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear", "Clear"),
    ]
    
    CSS = """
    Screen {
        layout: grid;
        grid-size: 1;
        grid-rows: 1fr auto;
    }
    
    #chat-container {
        height: 1fr;
        overflow-y: auto;
    }
    
    #input-container {
        height: auto;
        dock: bottom;
    }
    """
    
    def __init__(self, agent: ReActAgent, config: AppConfig):
        super().__init__()
        self.agent = agent
        self.config = config
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield ChatContainer(id="chat-container")
        yield ChatInput(id="input-container")
        yield Footer()
    
    async def on_chat_submit(self, event: ChatSubmit) -> None:
        """处理用户输入"""
        ...
    
    async def action_clear(self) -> None:
        """清空聊天"""
        ...
```

**必需功能**:
- [ ] 主应用框架
- [ ] 布局管理
- [ ] 键盘绑定
- [ ] 异步 LLM 调用（不阻塞 UI）
- [ ] 事件处理

#### 4.5.2 `widgets/chat.py` - 聊天组件

**职责**: 显示聊天消息

**类设计**:
```python
from textual.widget import Widget
from textual.reactive import reactive
from rich.markdown import Markdown

class ChatMessage(Widget):
    """单条聊天消息"""
    
    message: reactive[str] = reactive("")
    role: reactive[str] = reactive("user")
    
    def __init__(self, message: str, role: str = "user"):
        super().__init__()
        self.message = message
        self.role = role
    
    def render(self) -> RenderableType:
        prefix = "👤" if self.role == "user" else "🤖"
        return Markdown(f"**{prefix}** {self.message}")

class ChatContainer(Widget):
    """聊天容器"""
    
    def compose(self) -> ComposeResult:
        yield Vertical()
    
    def add_message(self, message: str, role: str) -> None:
        """添加消息"""
        ...
    
    def clear(self) -> None:
        """清空聊天"""
        ...
```

**必需功能**:
- [ ] 消息显示（用户/助手/系统）
- [ ] Markdown 渲染
- [ ] 自动滚动
- [ ] 消息添加和清空

#### 4.5.3 `widgets/input.py` - 输入组件

**职责**: 用户输入和命令解析

**类设计**:
```python
from textual.widgets import Input
from textual.message import Message

class ChatSubmit(Message):
    """聊天提交消息"""
    def __init__(self, text: str):
        super().__init__()
        self.text = text

class ChatInput(Input):
    """聊天输入框"""
    
    def __init__(self):
        super().__init__(
            placeholder="Type a message or /command...",
            submit_on_enter=True
        )
    
    def on_submitted(self, event: Input.Submitted) -> None:
        """处理提交"""
        text = event.value.strip()
        if text:
            self.post_message(ChatSubmit(text))
            self.value = ""
```

**必需功能**:
- [ ] 文本输入
- [ ] 回车提交
- [ ] 命令检测（`/` 开头）
- [ ] 输入历史（可选）

#### 4.5.4 命令系统

**支持的命令**:

| 命令 | 说明 | 示例 |
|------|------|------|
| `/help` | 显示帮助 | `/help` |
| `/clear` | 清空聊天 | `/clear` |
| `/models` | 列出可用模型 | `/models` |
| `/models use <name>` | 切换模型 | `/models use deepseek-pro` |
| `/models info` | 显示当前模型信息 | `/models info` |
| `/memory` | 显示记忆信息 | `/memory` |
| `/memory search <query>` | 搜索记忆 | `/memory search Python` |
| `/quit` | 退出程序 | `/quit` |

**命令解析器**:
```python
class CommandParser:
    """命令解析器"""
    
    def parse(self, text: str) -> tuple[str, list[str]] | None:
        """解析命令，返回 (command, args) 或 None"""
        if not text.startswith("/"):
            return None
        parts = text.split()
        return parts[0], parts[1:]
```

---

### 4.6 配置模块 (`src/lukawi/config/`)

#### 4.6.1 `models.py` - 配置模型

**Pydantic 模型**:
```python
from pydantic import BaseModel, Field
from typing import Optional

class DeepSeekConfig(BaseModel):
    api_key: str = ""
    model: str = "deepseek-v4-flash"
    base_url: str = "https://api.deepseek.com"
    max_tokens: int = 4096
    temperature: float = 0.7

class ModelConfig(BaseModel):
    default: str = "deepseek"
    providers: dict[str, DeepSeekConfig] = {
        "deepseek": DeepSeekConfig()
    }

class ToolProfileConfig(BaseModel):
    allowed_tools: list[str] = ["*"]
    denied_tools: list[str] = []

class ToolPolicyConfig(BaseModel):
    default_profile: str = "default"
    profiles: dict[str, ToolProfileConfig] = {
        "default": ToolProfileConfig()
    }

class MemoryConfig(BaseModel):
    enabled: bool = True
    db_path: str = "memory.db"
    session_max_messages: int = 100
    longterm_enabled: bool = True

class AgentConfig(BaseModel):
    max_steps: int = 10
    max_tokens: int = 10000
    loop_detection: bool = True
    loop_threshold: int = 3

class AppConfig(BaseModel):
    model: ModelConfig = ModelConfig()
    tools: ToolPolicyConfig = ToolPolicyConfig()
    memory: MemoryConfig = MemoryConfig()
    agent: AgentConfig = AgentConfig()
    
    @classmethod
    def from_yaml(cls, path: str) -> "AppConfig":
        """从 YAML 文件加载配置"""
        ...
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """从环境变量加载配置"""
        ...
```

**必需功能**:
- [ ] 所有配置模型定义
- [ ] 默认值设置
- [ ] YAML 加载
- [ ] 环境变量加载
- [ ] 配置验证

#### 4.6.2 `settings.py` - 配置加载器

**职责**: 加载和合并配置

**类设计**:
```python
class Settings:
    """配置加载器"""
    
    def __init__(self, config_path: str | None = None):
        self.config_path = config_path or "config/default.yaml"
        self._config: AppConfig | None = None
    
    def load(self) -> AppConfig:
        """加载配置"""
        # 1. 加载默认配置
        # 2. 加载用户配置（如果存在）
        # 3. 合并环境变量
        # 4. 验证配置
        ...
    
    def get(self) -> AppConfig:
        """获取配置（懒加载）"""
        if self._config is None:
            self._config = self.load()
        return self._config
    
    def _expand_env_vars(self, value: str) -> str:
        """展开环境变量"""
        ...
```

**必需功能**:
- [ ] 配置文件加载
- [ ] 环境变量展开（`${VAR}` 语法）
- [ ] 配置合并
- [ ] 验证和错误处理

---

### 4.7 工具函数 (`src/lukawi/utils/`)

#### 4.7.1 `logging.py` - 日志系统

```python
import logging
from rich.logging import RichHandler

def setup_logging(level: str = "INFO") -> None:
    """设置日志"""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True)]
    )

def get_logger(name: str) -> logging.Logger:
    """获取 logger"""
    return logging.getLogger(name)
```

**必需功能**:
- [ ] Rich 格式化
- [ ] 日志级别配置
- [ ] 文件输出（可选）

#### 4.7.2 `helpers.py` - 辅助函数

```python
from pathlib import Path

def safe_path(path: str | Path) -> Path:
    """安全路径处理（Windows 兼容）"""
    return Path(path).resolve()

def read_text(path: str | Path, encoding: str = "utf-8") -> str:
    """读取文本文件"""
    return safe_path(path).read_text(encoding=encoding)

def write_text(path: str | Path, content: str, encoding: str = "utf-8") -> None:
    """写入文本文件"""
    path = safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)

def truncate_text(text: str, max_length: int = 1000) -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
```

**必需功能**:
- [ ] 路径安全处理
- [ ] 文件读写
- [ ] 文本截断
- [ ] Windows 兼容

---

## 5. API 接口规范

### 5.1 LLM API 调用格式

**DeepSeek API 端点**: `https://api.deepseek.com/v1/chat/completions`

**请求格式**:
```json
{
  "model": "deepseek-v4-flash",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "web_fetch",
        "description": "Fetch content from a URL",
        "parameters": {
          "type": "object",
          "properties": {
            "url": {"type": "string", "description": "URL to fetch"}
          },
          "required": ["url"]
        }
      }
    }
  ],
  "temperature": 0.7,
  "max_tokens": 4096,
  "stream": false
}
```

**响应格式**:
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "deepseek-v4-flash",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_xxx",
            "type": "function",
            "function": {
              "name": "web_fetch",
              "arguments": "{\"url\": \"https://example.com\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150
  }
}
```

### 5.2 工具调用格式

**LLM 输出的工具调用 JSON**:
```json
{
  "thinking": "用户想要查询天气信息，我需要使用 web_fetch 工具",
  "action": {
    "tool": "web_fetch",
    "parameters": {
      "url": "https://api.weather.com/current",
      "format": "json"
    }
  }
}
```

**工具结果返回格式**:
```json
{
  "tool": "web_fetch",
  "status": "success",
  "result": {
    "content": "...",
    "metadata": {
      "status_code": 200,
      "content_type": "application/json"
    }
  }
}
```

---

## 6. 数据模型规范

### 6.1 消息模型

```python
class Message(BaseModel):
    role: MessageRole  # system, user, assistant, tool
    content: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] | None = None
    name: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)
```

### 6.2 工具模型

```python
class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: list[ToolParameter]
    category: str = "general"
    tags: list[str] = []
    
    class Config:
        frozen = True  # 不可变

class ToolParameter(BaseModel):
    name: str
    type: ToolParameterType
    description: str
    required: bool = True
    default: Any = None
    enum: list[Any] | None = None
```

### 6.3 配置模型

```python
class AppConfig(BaseModel):
    model: ModelConfig = Field(default_factory=ModelConfig)
    tools: ToolPolicyConfig = Field(default_factory=ToolPolicyConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
```

---

## 7. 测试规范

### 7.1 测试结构

```
tests/
├── conftest.py                # 共享 fixtures
├── test_agent/
│   ├── test_core.py          # ReAct 循环测试
│   └── test_executor.py      # 工具网关测试
├── test_llm/
│   ├── test_deepseek.py      # DeepSeek 提供者测试
│   └── test_registry.py      # 模型注册表测试
├── test_tools/
│   ├── test_registry.py      # 工具注册表测试
│   ├── test_policy.py        # 策略管道测试
│   ├── test_executor.py      # 执行器测试
│   └── test_builtin/
│       ├── test_web_fetch.py
│       ├── test_file_ops.py
│       └── test_shell.py
├── test_memory/
│   ├── test_session.py
│   ├── test_longterm.py
│   └── test_manager.py
├── test_tui/
│   ├── test_app.py
│   └── test_commands.py
└── test_integration/
    └── test_e2e.py           # 端到端测试
```

### 7.2 测试策略

| 层级 | 覆盖率目标 | 工具 | 说明 |
|------|-----------|------|------|
| 单元测试 | 90%+ | pytest | 每个模块独立测试 |
| 集成测试 | 80%+ | pytest + respx | 模块交互测试 |
| 端到端测试 | 关键流程 | pytest | 完整 ReAct 循环 |
| 手动测试 | N/A | TUI | 视觉验证 |

### 7.3 测试 Fixtures

```python
# conftest.py
import pytest
from lukawi.llm.mock import MockProvider
from lukawi.tools.registry import ToolRegistry
from lukawi.memory.manager import MemoryManager

@pytest.fixture
def mock_llm():
    """Mock LLM 提供者"""
    return MockProvider()

@pytest.fixture
def tool_registry():
    """工具注册表"""
    registry = ToolRegistry()
    # 注册测试工具
    return registry

@pytest.fixture
def memory_manager(tmp_path):
    """记忆管理器"""
    return MemoryManager(db_path=str(tmp_path / "test.db"))

@pytest.fixture
def app_config(tmp_path):
    """测试配置"""
    config = AppConfig()
    config.memory.db_path = str(tmp_path / "test.db")
    return config
```

### 7.4 测试命名规范

```python
# 测试文件命名
test_<module>.py

# 测试函数命名
test_<功能>_<场景>_<预期结果>

# 示例
def test_chat_normal_returns_response():
def test_chat_tool_call_returns_tool_result():
def test_tool_registry_register_adds_tool():
def test_tool_policy_deny_blocks_tool():
```

---

## 8. 代码风格规范

### 8.1 格式化工具

- **Linter**: ruff
- **格式化**: ruff format
- **类型检查**: mypy

### 8.2 配置

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.10"
strict = true
```

### 8.3 命名约定

| 类型 | 风格 | 示例 |
|------|------|------|
| 模块 | snake_case | `tool_registry.py` |
| 类 | PascalCase | `ToolRegistry` |
| 函数 | snake_case | `get_tool()` |
| 变量 | snake_case | `tool_name` |
| 常量 | UPPER_CASE | `MAX_TOKENS` |
| 私有 | _leading_underscore | `_internal_method()` |

### 8.4 导入顺序

```python
# 1. 标准库
import asyncio
from pathlib import Path

# 2. 第三方库
from pydantic import BaseModel
import httpx

# 3. 本地模块
from lukawi.tools.base import ToolDefinition
from lukawi.utils.helpers import safe_path
```

### 8.5 文档字符串

```python
def execute_tool(
    tool_name: str,
    parameters: dict,
    timeout: float = 30.0
) -> ToolResult:
    """执行工具并返回结果。
    
    Args:
        tool_name: 工具名称
        parameters: 工具参数
        timeout: 超时时间（秒）
    
    Returns:
        ToolResult: 工具执行结果
    
    Raises:
        ToolNotFoundError: 工具不存在
        ToolTimeoutError: 执行超时
    """
    ...
```

---

## 9. 提交规范

### 9.1 Commit Message 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型**:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档
- `style`: 格式（不影响代码运行）
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

**示例**:
```
feat(tools): add web_fetch builtin tool

- Implement HTTP GET/POST requests
- Convert HTML to markdown
- Handle timeouts and errors

Closes #123
```

### 9.2 分支策略

- `main`: 稳定版本
- `develop`: 开发分支
- `feature/*`: 功能分支
- `fix/*`: 修复分支

---

## 10. 开发检查清单

### 10.1 Phase 0: 项目脚手架 ✅

- [x] 创建 pyproject.toml
- [x] 创建目录结构
- [x] 创建 .gitignore
- [x] 初始化 Git 仓库
- [ ] 创建 README.md
- [ ] 创建默认配置文件
- [ ] 验证 pip install -e . 可用

### 10.2 Phase 1: 配置与核心抽象

- [ ] 实现 config/models.py
  - [ ] AppConfig 模型
  - [ ] ModelConfig 模型
  - [ ] ToolPolicyConfig 模型
  - [ ] MemoryConfig 模型
  - [ ] AgentConfig 模型
- [ ] 实现 config/settings.py
  - [ ] YAML 加载
  - [ ] 环境变量展开
  - [ ] 配置合并
- [ ] 实现 tools/base.py
  - [ ] ToolParameter 定义
  - [ ] ToolDefinition 定义
  - [ ] ToolResult 定义
  - [ ] OpenAI Schema 转换
- [ ] 实现 llm/base.py
  - [ ] LLMProvider ABC
  - [ ] Message 类型
  - [ ] LLMResponse 类型
- [ ] 实现 utils/logging.py
  - [ ] Rich 日志配置
- [ ] 实现 utils/helpers.py
  - [ ] 路径处理
  - [ ] 文件读写
- [ ] 所有测试通过

### 10.3 Phase 2: DeepSeek LLM 集成

- [ ] 实现 llm/deepseek.py
  - [ ] OpenAI SDK 调用
  - [ ] 工具调用支持
  - [ ] 流式响应
  - [ ] 错误处理
- [ ] 实现 llm/mock.py
  - [ ] 预设响应
  - [ ] 调用记录
- [ ] 实现 llm/registry.py
  - [ ] 提供者注册
  - [ ] 运行时切换
- [ ] 所有测试通过

### 10.4 Phase 3: 工具系统

- [ ] 实现 tools/registry.py
  - [ ] 工具注册
  - [ ] 工具查找
  - [ ] 装饰器支持
- [ ] 实现 tools/policy.py
  - [ ] 3 层过滤
  - [ ] 通配符支持
- [ ] 实现 tools/executor.py
  - [ ] 钩子系统
  - [ ] 超时控制
- [ ] 实现 tools/builtin/web_fetch.py
  - [ ] HTTP 请求
  - [ ] HTML → Markdown
- [ ] 实现 tools/builtin/file_ops.py
  - [ ] 文件读写
  - [ ] 路径安全
- [ ] 实现 tools/builtin/shell.py
  - [ ] 命令执行
  - [ ] Windows 兼容
- [ ] 所有测试通过

### 10.5 Phase 4: Agent 核心

- [ ] 实现 agent/core.py
  - [ ] ReAct 循环
  - [ ] 预算控制
  - [ ] 循环检测
  - [ ] 事件流
- [ ] 实现 agent/executor.py
  - [ ] 工具网关
  - [ ] 策略集成
- [ ] 集成测试通过

### 10.6 Phase 5: 记忆系统

- [ ] 实现 memory/session.py
  - [ ] 会话存储
  - [ ] 上下文窗口
- [ ] 实现 memory/longterm.py
  - [ ] SQLite 存储
  - [ ] 记忆 CRUD
- [ ] 实现 memory/manager.py
  - [ ] 统一接口
  - [ ] 用户隔离
- [ ] 所有测试通过

### 10.7 Phase 6: TUI

- [ ] 实现 tui/app.py
  - [ ] 主应用框架
  - [ ] 布局管理
- [ ] 实现 tui/widgets/chat.py
  - [ ] 消息显示
  - [ ] Markdown 渲染
- [ ] 实现 tui/widgets/input.py
  - [ ] 输入处理
  - [ ] 命令检测
- [ ] 实现命令系统
  - [ ] /help
  - [ ] /clear
  - [ ] /models
  - [ ] /memory
- [ ] 实现 main.py 入口
- [ ] TUI 可正常运行

### 10.8 Phase 7: MCP & Skills

- [ ] 实现 mcp/client.py
  - [ ] stdio 传输
  - [ ] SSE 传输
- [ ] 实现 mcp/server.py
  - [ ] 工具暴露
- [ ] 实现 skills/loader.py
  - [ ] SKILL.md 解析
- [ ] 实现 skills/executor.py
  - [ ] 技能注入
- [ ] 创建示例技能
- [ ] 所有测试通过

### 10.9 Phase 8: 集成与优化

- [ ] 依赖注入和连接
- [ ] 错误处理完善
- [ ] 流式响应显示
- [ ] 工具执行显示
- [ ] Windows 兼容性测试
- [ ] 端到端测试通过

### 10.10 Phase 9: 打包与发布

- [ ] 完善 pyproject.toml
- [ ] 编写用户文档
- [ ] 编写开发者文档
- [ ] 所有测试通过
- [ ] Lint 和类型检查通过
- [ ] pip install 测试通过

---

## 附录 A: 参考资源

| 资源 | 链接 | 用途 |
|------|------|------|
| DeepSeek API | https://platform.deepseek.com/api-docs | LLM 集成 |
| Textual 文档 | https://textual.textualize.io/ | TUI 开发 |
| Pydantic 文档 | https://docs.pydantic.dev/ | 数据模型 |
| httpx 文档 | https://www.python-httpx.org/ | HTTP 客户端 |
| Pi Agent | https://github.com/earendil-works/pi | 架构参考 |
| OpenClaw | https://github.com/openclaw/openclaw | 工具策略参考 |
| DeepSeek-TUI | https://github.com/Hmbown/DeepSeek-TUI | Hook 系统参考 |

---

## 附录 B: 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | (无) |
| `LUKAWI_MODEL` | 默认模型 | `deepseek-v4-flash` |
| `LUKAWI_CONFIG` | 配置文件路径 | `config/default.yaml` |
| `LUKAWI_LOG_LEVEL` | 日志级别 | `INFO` |
| `LUKAWI_MEMORY_DB` | 记忆数据库路径 | `memory.db` |

---

## 附录 C: 错误码

| 错误码 | 说明 | 处理方式 |
|--------|------|----------|
| `TOOL_NOT_FOUND` | 工具不存在 | 返回错误给 LLM |
| `TOOL_DENIED` | 工具被策略拒绝 | 返回错误给 LLM |
| `TOOL_TIMEOUT` | 工具执行超时 | 返回错误给 LLM |
| `LLM_ERROR` | LLM 调用失败 | 重试或返回错误 |
| `CONFIG_ERROR` | 配置错误 | 使用默认配置 |
| `MEMORY_ERROR` | 记忆系统错误 | 降级到无记忆模式 |

---

**文档结束**

如有疑问，请查阅 CLAUDE.md 或联系项目维护者。
