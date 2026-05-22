# Lukawi Agent Framework - 项目理解与设计规范

## 项目概述

从零构建一个 AI Agent 框架，核心能力：
- 接收用户自然语言指令
- 自主选择合适工具
- 调用工具并获取结果
- 整理结果后回复用户
- 支持多轮"思考-行动"循环（ReAct 模式）

## 硬性约束

### 平台适配
- **首要适配 Windows 系统** - 所有代码、路径处理、依赖必须在 Windows 上正常运行
- 使用 `pathlib` 处理路径，避免硬编码 Unix 路径分隔符
- 考虑 Windows 编码问题（UTF-8 优先）
- 依赖安装使用 pip/uv，确保 Windows 兼容性

### 禁止事项
- **禁止直接复用** OpenClaw、LangChain 等高级框架
- 可以**借鉴设计模式**，但必须自己实现核心逻辑
- 可以直接使用的"轮子"：web_fetch 工具、成熟的记忆框架（如 Mem0）

## 技术栈决策

### 语言选择：Python
- 理由：生态丰富，AI/ML 库支持最好，快速原型开发
- 版本：Python 3.10+（支持现代语法特性）

### TUI 框架：Textual + Rich
- Textual：现代 Python TUI 框架，类似 Web 的组件模型
- Rich：终端富文本渲染
- 理由：跨平台（Windows 原生支持），API 简洁

### 记忆系统：本地轻量化记忆系统
- 设计：完全本地实现，不依赖外部云服务
- 架构：SQLite 存储 + 本地向量检索（可选）
- 会话隔离：通过 `user_id` + `session_id` + `agent_id` 多维作用域
- 功能：会话记忆、工作记忆、长期记忆（渐进式摘要）

### LLM 集成：原生 DeepSeek API
- 端点：`https://api.deepseek.com/beta/chat/completions`
- 默认模型：deepseek-v4-flash / deepseek-v4-pro
- 模型切换：类似 OpenCode 的 `/models` 命令
- **Mock 模式**：开发测试时使用 mock 响应，无需真实 API 密钥
- **API 密钥配置**：支持通过配置文件或环境变量设置

## 架构设计

### 核心模块

```
lukawi-agent/
├── CLAUDE.md               # 本文件 - 项目理解与规范
├── README.md               # 项目说明
├── pyproject.toml          # 项目配置与依赖
├── src/
│   └── lukawi/
│       ├── __init__.py
│       ├── main.py         # 入口点
│       ├── agent/          # Agent 核心引擎
│       │   ├── __init__.py
│       │   ├── core.py     # ReAct 循环实现
│       │   ├── planner.py  # 任务规划
│       │   └── executor.py # 执行器
│       ├── llm/            # LLM 抽象层
│       │   ├── __init__.py
│       │   ├── base.py     # 基础接口
│       │   ├── deepseek.py # DeepSeek 实现
│       │   └── registry.py # 模型注册表
│       ├── tools/          # 工具管理系统
│       │   ├── __init__.py
│       │   ├── base.py     # 工具基类
│       │   ├── registry.py # 工具注册表
│       │   ├── policy.py   # 工具策略（借鉴 OpenClaw）
│       │   └── builtin/    # 内置工具
│       │       ├── __init__.py
│       │       ├── web_fetch.py
│       │       ├── file_ops.py
│       │       └── shell.py
│       ├── memory/         # 记忆系统
│       │   ├── __init__.py
│       │   ├── manager.py  # 记忆管理器
│       │   ├── session.py  # 会话记忆
│       │   └── longterm.py # 长期记忆
│       ├── mcp/            # MCP 接口
│       │   ├── __init__.py
│       │   ├── client.py   # MCP 客户端
│       │   └── server.py   # MCP 服务器
│       ├── skills/         # Agent Skills 系统
│       │   ├── __init__.py
│       │   ├── loader.py   # 技能加载器
│       │   └── executor.py # 技能执行器
│       ├── tui/            # 终端界面
│       │   ├── __init__.py
│       │   ├── app.py      # Textual 应用
│       │   ├── widgets/    # 自定义组件
│       │   └── themes/     # 主题配置
│       ├── config/         # 配置管理
│       │   ├── __init__.py
│       │   ├── settings.py # 设置管理
│       │   └── models.py   # 配置模型
│       └── utils/          # 工具函数
│           ├── __init__.py
│           ├── logging.py  # 日志系统
│           └── helpers.py  # 辅助函数
├── tests/                  # 测试目录
├── docs/                   # 文档
└── skills/                 # 内置技能文件
    └── web_search/
        └── SKILL.md
```

### 设计模式借鉴

#### 1. Pi 的 ExecutionEnv 抽象
```python
from abc import ABC, abstractmethod
from pathlib import Path

class ExecutionEnv(ABC):
    """文件系统和进程执行环境的抽象接口"""
    
    @abstractmethod
    async def exec(self, command: str, cwd: str = None) -> tuple[str, str, int]:
        """执行命令，返回 (stdout, stderr, exit_code)"""
        ...
    
    @abstractmethod
    async def read_text_file(self, path: str) -> str:
        """读取文本文件"""
        ...
    
    @abstractmethod
    async def write_file(self, path: str, content: str) -> None:
        """写入文件"""
        ...
```

#### 2. OpenClaw 的工具策略管道
```python
class ToolPolicy:
    """多阶段工具过滤策略"""
    
    def filter_tools(self, tools: list[Tool], context: Context) -> list[Tool]:
        tools = self._apply_profile_filter(tools, context.profile)
        tools = self._apply_allow_deny(tools, context.config)
        tools = self._apply_provider_restrictions(tools, context.provider)
        return tools
```

#### 3. DeepSeek-TUI 的 Hook 系统
```python
class ToolHooks:
    """工具执行前后的钩子"""
    
    async def pre_execute(self, tool: Tool, params: dict) -> bool:
        """执行前钩子，返回 False 可阻止执行"""
        ...
    
    async def post_execute(self, tool: Tool, result: ToolResult) -> None:
        """执行后钩子，用于日志、诊断等"""
        ...
```

## 工具调用格式

### LLM 输出格式（JSON 结构化）
```json
{
  "thinking": "用户想要查询天气信息，我需要使用 web_fetch 工具...",
  "action": {
    "tool": "web_fetch",
    "parameters": {
      "url": "https://api.weather.com/current",
      "method": "GET"
    }
  }
}
```

### 工具结果返回格式
```json
{
  "tool": "web_fetch",
  "status": "success",
  "result": {
    "content": "...",
    "metadata": {}
  }
}
```

## 记忆系统设计

### 三层记忆架构

| 层级 | 存储位置 | 生命周期 | 用途 |
|------|----------|----------|------|
| 会话记忆 | 内存 | 单次会话 | 当前对话上下文 |
| 工作记忆 | SQLite | 数小时 | 多步任务中间状态 |
| 长期记忆 | 向量数据库 | 永久 | 用户偏好、历史知识 |

### 会话隔离机制
```python
memory.add(
    messages,
    user_id="user_123",      # 用户隔离
    agent_id="lukawi",       # Agent 隔离
    session_id="session_456" # 会话隔离
)
```

### 本地记忆存储
```python
# SQLite 存储结构
memory_db/
├── sessions.db      # 会话记忆
├── working.db       # 工作记忆（多步任务状态）
└── longterm.db      # 长期记忆（用户偏好、历史知识）
```

## 模型切换机制

### 配置文件 (config.yaml)
```yaml
models:
  default: deepseek-flash
  available:
    - name: deepseek-flash
      provider: deepseek
      model: deepseek-v4-flash
      api_key: ${DEEPSEEK_API_KEY}
    - name: deepseek-pro
      provider: deepseek
      model: deepseek-v4-pro
      api_key: ${DEEPSEEK_API_KEY}
    - name: local-ollama
      provider: ollama
      model: llama3
      base_url: http://localhost:11434
```

### TUI 切换命令
```
/models                    # 列出可用模型
/models use deepseek-pro   # 切换到指定模型
/models info               # 显示当前模型信息
```

## 开发阶段规划

### Phase 1: 基础框架
- [ ] 项目脚手架搭建
- [ ] 核心 Agent 循环（ReAct）
- [ ] DeepSeek API 集成
- [ ] 基础工具系统

### Phase 2: 工具与记忆
- [ ] web_fetch 工具实现
- [ ] 文件操作工具
- [ ] Mem0 记忆系统集成
- [ ] 会话管理

### Phase 3: TUI 与交互
- [ ] Textual TUI 开发
- [ ] 模型切换功能
- [ ] 命令系统

### Phase 4: 高级功能
- [ ] MCP 接口支持
- [ ] Agent Skills 系统
- [ ] 工具策略管道

### Phase 5: 打包与发布
- [ ] 测试覆盖
- [ ] 文档编写
- [ ] 打包为可安装包

## 参考资源

- [Mem0 文档](https://docs.mem0.ai/)
- [DeepSeek API 文档](https://platform.deepseek.com/api-docs)
- [Textual 文档](https://textual.textualize.io/)
- [Pi Agent 源码](https://github.com/earendil-works/pi)
- [OpenClaw 源码](https://github.com/openclaw/openclaw)

## 决策记录

| 日期 | 决策 | 理由 |
|------|------|------|
| 2026-05-13 | 选择 Python 而非 TypeScript | AI/ML 生态更好，快速原型 |
| 2026-05-13 | 选择 Textual 而非 Bubble Tea | Windows 原生支持，Python 生态 |
| 2026-05-13 | 选择 Mem0 作为记忆系统 | 最成熟，文档完善 |
| 2026-05-13 | 首要适配 Windows | 用户明确要求 |
