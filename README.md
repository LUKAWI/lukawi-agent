# Lukawi Agent

[English](#english) | [中文](#chinese) | [详细中文文档 →](./README_CN.md)

---

<a id="english"></a>
## 🇬🇧 English

A lightweight, extensible AI Agent framework with ReAct loop, tool calling, memory, and knowledge base. Fully local — everything except API calls runs on your machine.

### Features

- **ReAct Loop Agent** — reasoning + acting with automatic tool calling
- **Streaming Chat** — token-by-token real-time output in WebUI
- **Tool System** — built-in tools: web fetch, file operations, shell commands
- **Extensible Skills** — drop `SKILL.md` files to teach the agent new abilities
- **MCP Protocol** — connect external tool servers (sequential thinking, code context, etc.)
- **Memory** — session-based short-term + persistent long-term memory with search
- **RAG Knowledge Base** — upload documents, semantic search via DashScope embeddings
- **WebUI** — React + TypeScript chat interface with Tailwind CSS, GSAP animations, model switching, session management
- **ChromaDB** — vector database for document retrieval, runs locally

---

### Quick Start

#### 1. Install

```bash
pip install lukawi
```

#### 2. Initialize

```bash
lukawi-init
```

This interactive wizard (bilingual EN/ZH) will guide you through:
- **LLM Provider** — Press Enter for DeepSeek (default), or provide your own OpenAI-compatible API:
  - Custom Base URL (e.g. `https://api.openai.com/v1`)
  - Model ID (e.g. `gpt-4`, `claude-3-opus`)
  - API Key
- **DashScope API Key** — optional, for document upload & semantic search
- **MCP Servers** — optional, select presets with Space key:
  - `sequential-thinking` — step-by-step reasoning for complex problems
  - `context7` — up-to-date library documentation
  - `tavily` — real-time web search (requires [Tavily API Key](https://app.tavily.com))

All keys are stored in a local `.env` file in the project root. They are **never** sent anywhere except to the API providers you configure.

#### 3. Launch

```bash
# Web UI (recommended)
lukawi webui

# Terminal REPL
lukawi
```

Open **http://localhost:50109** in your browser.

#### 4. Add Skills (optional)

Drop `SKILL.md` files into the `skills/` directory:

```
skills/
├── my-skill/
│   └── SKILL.md
```

Restart the agent to load new skills.

---

### Configuration

Default configuration is bundled inside the package. Override with a local config file or `.env`:

```env
# DeepSeek (default) or use CUSTOM_MODEL_* for custom API
DEEPSEEK_API_KEY=sk-...

# Optional: custom OpenAI-compatible API
CUSTOM_MODEL_BASE_URL=https://api.openai.com/v1
CUSTOM_MODEL_ID=gpt-4
CUSTOM_MODEL_API_KEY=sk-...

# Optional: DashScope for RAG / Knowledge Base
DASHSCOPE_API_KEY=sk-...

# Optional: Tavily for web search
TAVILY_API_KEY=tvly-...
```

MCP servers are managed via `lukawi-init` and stored in `~/.lukawi/mcp-servers.json`.

| Config File | Location |
|---|---|
| `.env` | Project root |
| `mcp-servers.json` | `~/.lukawi/mcp-servers.json` |
| Memory DB | `~/.lukawi/memory.db` |
| ChromaDB | `~/.lukawi/chroma_db/` |

---

### CLI Commands

| Command | Description |
|---|---|
| `lukawi` | Start interactive terminal REPL |
| `lukawi webui` | Launch Web UI (default: http://localhost:50109) |
| `lukawi chat "message"` | One-shot chat message |
| `lukawi models` | List and switch LLM models |
| `lukawi config` | View and edit configuration |
| `lukawi skills` | Manage skills |
| `lukawi status` | Show agent status |
| `lukawi --version` | Show version |
| `lukawi-init` | Run setup wizard |

---

### Keyboard Shortcuts (WebUI)

| Shortcut | Action |
|---|---|
| `Ctrl+B` | Toggle sidebar |
| `Ctrl+L` | Clear chat / new session |
| `Enter` | Send message |
| `Shift+Enter` | New line |
| `/` | Command mode |

---

### Development

```bash
git clone https://github.com/LUKAWI/lukawi-agent.git
cd lukawi-agent
pip install -e ".[dev]"

# Run tests
python -m pytest

# Build frontend
cd web && npm install && npm run build
```

---

### License

MIT — see [LICENSE](./LICENSE)

---

<a id="chinese"></a>
## 🇨🇳 中文

一款轻量级、可扩展的 AI Agent 框架，具备 ReAct 推理循环、工具调用、记忆和知识库功能。除 API 调用外，所有数据完全本地运行。

### 功能特性

- **ReAct 循环 Agent** — 推理 + 行动，自动工具调用
- **流式输出** — WebUI 中逐 token 实时输出
- **工具系统** — 内置工具：网页抓取、文件操作、Shell 命令
- **可扩展技能** — 放入 `SKILL.md` 文件即可教会 Agent 新能力
- **MCP 协议** — 连接外部工具服务器（分步推理、代码上下文等）
- **记忆系统** — 基于会话的短期记忆 + 持久化长期记忆，支持搜索
- **RAG 知识库** — 上传文档，通过 DashScope 嵌入做语义搜索
- **WebUI** — 基于 React + TypeScript 的聊天界面，Tailwind CSS + GSAP 动画，支持模型切换、会话管理
- **ChromaDB** — 本地运行的向量数据库，用于文档检索

---

### 快速开始

#### 1. 安装

```bash
pip install lukawi
```

#### 2. 初始化

```bash
lukawi-init
```

交互式配置向导（支持中/英文）会引导你配置：
- **DeepSeek API Key** — 必填，用于 LLM 对话
- **DashScope API Key** — 可选，用于文档上传和语义搜索
- **MCP 服务器** — 可选，用空格键选择预设：
  - `sequential-thinking` — 将复杂问题拆解为分步推理
  - `context7` — 提供最新库文档和代码上下文
  - `tavily` — 实时网络搜索（需要 [Tavily API Key](https://app.tavily.com)）

所有密钥保存在本地 `.env` 文件中，**绝不会**发送到你配置的 API 提供商以外的任何地方。

#### 3. 启动

```bash
# Web UI（推荐）
lukawi webui

# 终端 REPL
lukawi
```

浏览器打开 **http://localhost:50109**

#### 4. 添加技能（可选）

将 `SKILL.md` 文件放入 `skills/` 目录：

```
skills/
├── my-skill/
│   └── SKILL.md
```

重启 Agent 即可加载新技能。

---

### 配置说明

默认配置随包发布。可通过本地配置文件或 `.env` 覆盖：

```env
# 必填：DeepSeek API 密钥
DEEPSEEK_API_KEY=sk-...

# 可选：DashScope 密钥（用于 RAG 知识库）
DASHSCOPE_API_KEY=sk-...
```

MCP 服务器通过 `lukawi-init` 管理，配置存储在 `~/.lukawi/mcp-servers.json`。

| 配置文件 | 位置 |
|---|---|
| `.env` | 当前工作目录 |
| `mcp-servers.json` | `~/.lukawi/mcp-servers.json` |
| 记忆数据库 | `~/.lukawi/memory.db` |
| ChromaDB | `~/.lukawi/chroma_db/` |

---

### CLI 命令

| 命令 | 说明 |
|---|---|
| `lukawi` | 启动交互式终端 REPL |
| `lukawi webui` | 启动 Web UI（默认：http://localhost:50109） |
| `lukawi chat "消息"` | 单次对话 |
| `lukawi models` | 查看和切换 LLM 模型 |
| `lukawi config` | 查看和编辑配置 |
| `lukawi skills` | 管理技能 |
| `lukawi status` | 查看 Agent 状态 |
| `lukawi --version` | 显示版本号 |
| `lukawi-init` | 运行初始化向导 |

---

### WebUI 快捷键

| 快捷键 | 功能 |
|---|---|
| `Ctrl+B` | 切换侧边栏 |
| `Ctrl+L` | 清空聊天 / 新建会话 |
| `Enter` | 发送消息 |
| `Shift+Enter` | 换行 |
| `/` | 命令模式 |

---

### 开发指南

```bash
git clone https://github.com/LUKAWI/lukawi-agent.git
cd lukawi-agent
pip install -e ".[dev]"

# 运行测试
python -m pytest

# 构建前端
cd web && npm install && npm run build
```

---

### 许可证

MIT — 详见 [LICENSE](./LICENSE)
