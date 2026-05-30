# Lukawi Agent

> 一款轻量级、可扩展的 AI Agent 框架 —— 让任何人都能在本地运行自己的 AI 助手。

<p align="center">
  <strong>PyPI 安装</strong> → <code>pip install lukawi</code> → <code>lukawi-init</code> → <code>lukawi webui</code>
</p>

---

## 目录

- [项目简介](#项目简介)
- [核心架构](#核心架构)
- [功能特性](#功能特性)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [详细安装指南](#详细安装指南)
- [命令行参考](#命令行参考)
- [WebUI 使用说明](#webui-使用说明)
- [配置文件详解](#配置文件详解)
- [Skills 技能系统](#skills-技能系统)
- [MCP 协议集成](#mcp-协议集成)
- [RAG 知识库](#rag-知识库)
- [记忆系统](#记忆系统)
- [工具系统](#工具系统)
- [模型切换](#模型切换)
- [开发指南](#开发指南)
- [常见问题](#常见问题)
- [项目文件结构](#项目文件结构)

---

## 项目简介

Lukawi Agent 是一个完全本地化的 AI Agent 框架。你只需要提供 API 密钥，其余所有数据和计算都在你自己的机器上完成。它基于 **ReAct 推理循环**（Reasoning + Acting），能够自主规划、调用工具、查阅文档、记住上下文，最终完成你的任务。

### 设计理念

- **完全本地** — 除了 API 调用，所有数据（会话记录、文档、向量库）全部存储在你本机，不上传任何数据到第三方
- **离线优先** — ChromaDB 向量数据库、SQLite 记忆库均在本地运行，不需要云服务
- **可扩展** — 通过 Skills（SKILL.md）和 MCP 协议，随时为 Agent 添加新能力
- **开箱即用** — 一行 `pip install`，三步启动，无需复杂配置

---

## 核心架构

```
┌─────────────────────────────────────────────────┐
│                   WebUI (React)                   │
│             http://localhost:50109               │
└─────────────────────┬───────────────────────────┘
                      │ SSE / REST API
┌─────────────────────┴───────────────────────────┐
│               FastAPI Server                      │
│  routes.py  │  sse.py  │  state.py  │  app.py    │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────┐
│               ReAct Agent Core                    │
│    推理 → 决策 → 执行 → 观察 → 循环               │
│    core.py  │  planner.py  │  executor.py         │
└──┬──────────┬──────────┬──────────┬──────────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐
│ LLM  │ │Tools │ │Memory│ │RAG /     │
│DeepSe│ │Web   │ │SQLite│ │ChromaDB  │
│ek    │ │Fetch │ │Session│ │DashScope │
│Mock  │ │Shell │ │Long  │ │Embedder  │
│      │ │File  │ │Term  │ │          │
└──────┘ └──────┘ └──────┘ └──────────┘
```

### 数据流

1. 用户在 WebUI（或终端 REPL）中输入消息
2. FastAPI 通过 SSE（Server-Sent Events）接收请求
3. Agent 核心启动 ReAct 循环：读取系统 Prompt → 调用 LLM 推理 → 决策是否需要工具
4. 如需工具：调用工具执行器 → 将结果反馈给 LLM → 继续推理
5. 流式输出：每个 token 通过 SSE 实时推送到前端
6. 会话自动持久化到 SQLite（记忆库），文档存入 ChromaDB（知识库）

---

## 功能特性

| 模块 | 功能 | 技术选型 |
|---|---|---|
| **LLM 引擎** | 多模型支持、流式输出 | DeepSeek API、OpenAI 兼容接口 |
| **工具系统** | 网页抓取、文件读写、Shell 执行 | 内置工具 + MCP 扩展 |
| **记忆系统** | 短期会话记忆、长期持久化记忆 | aiosqlite、语义搜索 |
| **知识库（RAG）** | 文档上传、切片、向量化、语义检索 | ChromaDB、DashScope Embedding |
| **技能（Skills）** | 通过 SKILL.md 扩增提示词 | 声明式 YAML front-matter |
| **MCP 协议** | 接入外部工具服务器 | Model Context Protocol |
| **WebUI** | React + TypeScript 聊天界面、会话管理、文档管理 | React + TypeScript + Vite + Tailwind CSS + GSAP + SSE |
| **终端 REPL** | 命令行交互式对话 | Rich 美化输出 |
| **初始化向导** | 交互式配置 API 密钥和 MCP 服务器 | 终端原生输入（跨平台） |

---

## 环境要求

| 软件 | 最低版本 | 说明 |
|---|---|---|
| **Python** | 3.10+ | 建议 3.11 或更高 |
| **Node.js** | 18+（仅开发需要） | 构建前端时使用 |
| **操作系统** | Windows / macOS / Linux | 全平台支持 |
| **网络** | 需要访问 DeepSeek API | 建议稳定的网络连接 |

---

## 快速开始

### 三步启动

```bash
# 第一步：安装
pip install lukawi

# 第二步：初始化配置（交互式向导）
lukawi-init

# 第三步：启动 WebUI
lukawi webui
```

浏览器自动打开 **http://localhost:50109**，开始对话。

---

## 详细安装指南

### 方式一：PyPI 安装（推荐）

```bash
pip install lukawi
```

安装完成后会自动注册两个全局命令：

- `lukawi` — 主程序入口
- `lukawi-init` — 初始化配置向导

### 方式二：从源码安装（开发者）

```bash
git clone https://github.com/LUKAWI/lukawi-agent.git
cd lukawi-agent
pip install -e ".[dev]"
```

### 初始化向导详解

运行 `lukawi-init` 后，向导会依次引导你完成以下配置：

#### 第一步：LLM 模型配置（必填）

```
DeepSeek API Key: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- 获取地址：https://platform.deepseek.com/api_keys
- 这是 **必填项**，没有它 Agent 无法进行对话

#### 第二步：RAG 知识库配置（可选）

```
DashScope API Key: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- 获取地址：https://dashscope.console.aliyun.com/apiKey
- 这是 **可选项**，不填则无法使用文档上传和语义搜索功能

#### 第三步：MCP 服务器（可选）

使用 **空格键** 选中/取消，**回车键** 确认，**Esc 键** 跳过：

```
 > [x] sequential-thinking  — 将复杂问题拆解为分步推理
   [x] context7             — 提供最新库文档和代码上下文
   [ ] 添加自定义 MCP 服务器...
```

### 验证安装

```bash
lukawi --version    # 显示版本号
lukawi webui        # 启动服务，浏览器应自动打开
```

---

## 命令行参考

### 主命令

| 命令 | 说明 | 示例 |
|---|---|---|
| `lukawi` | 启动终端交互式 REPL | `lukawi` |
| `lukawi webui` | 启动 Web UI 服务器 | `lukawi webui` |
| `lukawi chat "消息"` | 单次对话（不进入 REPL） | `lukawi chat "你好"` |
| `lukawi models` | 查看和切换 LLM 模型 | `lukawi models` |
| `lukawi config` | 查看和编辑配置 | `lukawi config` |
| `lukawi skills` | 管理技能文件 | `lukawi skills` |
| `lukawi status` | 查看 Agent 运行状态 | `lukawi status` |
| `lukawi-init` | 运行初始化配置向导 | `lukawi-init` |
| `lukawi --version` | 显示版本号 | `lukawi --version` |

### 全局选项

| 选项 | 说明 |
|---|---|
| `--config PATH` | 指定配置文件路径（覆盖默认） |
| `--model NAME` | 指定要使用的模型名称 |
| `--debug` | 启用调试日志 |
| `--mock` | 使用 Mock 模型（无需 API Key，用于测试） |
| `--mcp PATH` | 指定 MCP 配置文件路径 |
| `--skills-dir PATH` | 指定 Skills 目录路径 |

### 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `LUKAWI_PORT` | WebUI 服务端口 | `50109` |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | — |
| `DASHSCOPE_API_KEY` | DashScope API 密钥 | — |

---

## WebUI 使用说明

### 界面概览

```
┌──────────┬──────────────────────────────────┐
│          │         Header（顶栏）            │
│ Sidebar  │  ┌────────────────────────────┐  │
│（侧边栏）│  │                            │  │
│          │  │      Chat Messages         │  │
│ • 会话   │  │      （聊天消息区域）        │  │
│ • 知识库 │  │                            │  │
│ • 技能   │  │  工具调用卡片（可展开）      │  │
│ • MCP    │  │                            │  │
│ • 快捷键 │  │                            │  │
│          │  └────────────────────────────┘  │
│          │      InputBar（输入栏）           │
│          │      StatusBar（状态栏）          │
└──────────┴──────────────────────────────────┘
```

### 快捷键

| 快捷键 | 功能 | 适用场景 |
|---|---|---|
| `Ctrl + B` | 展开/收起侧边栏 | 需要更多聊天空间时 |
| `Ctrl + L` | 清空聊天 / 新建会话 | 开始新话题 |
| `Enter` | 发送消息 | 日常输入 |
| `Shift + Enter` | 消息换行 | 多行输入 |
| `/` | 进入命令模式 | 快速执行操作 |

### 功能板块

**会话管理（Sessions Panel）**
- 创建新会话：点击侧边栏 "+" 按钮
- 切换会话：点击已有会话记录
- 删除会话：悬停后点击 × 按钮（需要二次确认）

**知识库（Knowledge Panel）**
- 上传文档：支持 `.txt`、`.md`、`.pdf` 等格式
- 查看状态：实时显示文档处理进度
- 删除文档：悬停后点击 × 按钮（需要二次确认）
- 文档会被自动切片、向量化并存入 ChromaDB

**技能列表（Skills Panel）**
- 浏览已加载的技能文件
- 点击可展开/折叠查看技能详情

**MCP 服务器（MCP Panel）**
- 显示已配置的 MCP 服务器列表
- 查看连接状态（已连接 / 未连接）

---

## 配置文件详解

### 默认配置

默认配置文件随包发布在 `src/lukawi/data/default.yaml`，用户无需手动创建。可通过 `.env` 文件或环境变量覆盖关键配置。

### .env 文件

在项目根目录创建 `.env` 文件（或运行 `lukawi-init` 自动生成）：

```env
# 必填项
DEEPSEEK_API_KEY=sk-your-deepseek-api-key

# 可选项（启用 RAG 知识库时需要）
DASHSCOPE_API_KEY=sk-your-dashscope-api-key
```

### 配置文件存储位置

| 文件 | 路径 | 用途 |
|---|---|---|
| `.env` | 当前工作目录 | API 密钥和关键配置 |
| `mcp-servers.json` | `~/.lukawi/mcp-servers.json` | MCP 服务器配置 |
| 记忆数据库 | `~/.lukawi/memory.db` | SQLite 持久化记忆 |
| ChromaDB | `~/.lukawi/chroma_db/` | 向量数据库（文档检索） |

### 完整配置项说明

```yaml
# config/default.yaml 中的主要配置项

model:                              # 模型配置
  default: deepseek                 # 默认使用的模型
  providers:                        # 模型提供者列表
    deepseek:
      api_key: ${DEEPSEEK_API_KEY}  # 从环境变量读取
      model: deepseek-v4-flash      # 模型名称
      base_url: https://api.deepseek.com
      max_tokens: 4096
      temperature: 0.7

agent:                              # Agent 行为配置
  max_steps: 10                     # 最大推理步数
  max_tokens: 100000                # 最大输出 token 数
  loop_detection: true              # 检测循环调用
  loop_threshold: 3                 # 循环检测阈值

tools:                              # 工具策略配置
  default_profile: default          # 默认工具策略
  profiles:
    default:                        # 默认策略
      allowed_tools: ["*"]          # 允许所有工具
      denied_tools: []              # 不禁用任何工具
    restricted:                     # 受限策略
      allowed_tools: ["web_fetch", "read_file", "list_dir"]
      denied_tools: ["exec_command", "write_file", "edit_file"]

memory:                             # 记忆配置
  enabled: true                     # 启用记忆系统
  session:
    max_messages: 100               # 每个会话最大消息数
  longterm:
    enabled: true                   # 启用长期记忆
    db_path: memory.db              # 数据库文件路径

rag:                                # 知识库配置
  enabled: true                     # 启用 RAG
  dashscope:                        # DashScope 嵌入模型
    api_key: ${DASHSCOPE_API_KEY}
    model: text-embedding-v3
    dimensions: 1024
  chroma_db_dir: ~/.lukawi/chroma_db
  chunk_size: 500                   # 文档切片大小
  chunk_overlap: 50                 # 切片重叠大小

tui:                                # UI 配置
  theme: light                      # 主题: light / dark
  show_sidebar: false               # 默认不展开侧边栏

mcp:                                # MCP 配置
  servers:                          # 预设 MCP 服务器
    - name: sequential-thinking
      command: ["npx", "-y", "@modelcontextprotocol/server-sequential-thinking"]
    - name: context7
      command: ["npx", "-y", "@upstash/context7-mcp"]

skills:                             # 技能配置
  directory: skills                 # 技能文件目录
  auto_load: true                   # 启动时自动加载
```

---

## Skills 技能系统

Skills 是 Lukawi 最灵活的扩展方式。只需创建一个 `SKILL.md` 文件，Agent 就能学会新能力。

### 技能文件格式

```
skills/
└── my-skill/
    └── SKILL.md
```

`SKILL.md` 使用 YAML front-matter + Markdown 格式：

```markdown
---
name: 代码审查专家
description: 对代码进行专业的代码审查，指出潜在问题
version: 1.0
auto_load: true
---

# 代码审查专家

你是一位资深的代码审查专家。当用户请求代码审查时，请遵循以下流程：

1. 先理解代码的功能和上下文
2. 检查潜在的 Bug 和安全漏洞
3. 评估代码的可读性和可维护性
4. 给出具体的改进建议

## 审查要点

- 变量命名是否清晰
- 错误处理是否完善
- 是否有性能瓶颈
- 是否符合最佳实践
```

### 技能生命周期

1. Agent 启动时扫描 `skills/` 目录
2. 解析 `SKILL.md` 中的 YAML front-matter 和 Markdown 内容
3. 将 Markdown 内容注入到系统 Prompt 中
4. 重启 Agent 后新技能生效

---

## MCP 协议集成

MCP（Model Context Protocol）允许 Agent 通过标准化协议连接外部工具服务器。

### 预设 MCP 服务器

| 名称 | 功能 | 安装方式 |
|---|---|---|
| **sequential-thinking** | 将复杂问题拆解为逐步推理 | 通过 `lukawi-init` 勾选，自动安装 |
| **context7** | 提供最新库文档和代码上下文 | 通过 `lukawi-init` 勾选，自动安装 |

### 添加自定义 MCP 服务器

在 `lukawi-init` 中选择 "添加自定义 MCP 服务器"，输入：

```
服务器名称: my-custom-server
启动命令: python
命令参数: my_mcp_server.py
```

配置存储在 `~/.lukawi/mcp-servers.json`：

```json
[
  {
    "name": "sequential-thinking",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
  },
  {
    "name": "context7",
    "command": "npx",
    "args": ["-y", "@upstash/context7-mcp"]
  }
]
```

---

## RAG 知识库

RAG（检索增强生成）让 Agent 能够根据你上传的文档内容回答问题。

### 工作流程

1. **上传** — 用户通过 WebUI 上传 `.txt`、`.md`、`.pdf` 文档
2. **切片** — 文档按 `chunk_size=500` 字符切分为语义块，重叠 `50` 字符
3. **向量化** — 通过 DashScope `text-embedding-v3` 模型转为 1024 维向量
4. **存储** — 向量存入本地 ChromaDB
5. **检索** — 用户提问时，检索最相关的 Top-K 文档片段
6. **增强** — 相关片段注入到 LLM 上下文，辅助回答

### 配置要点

```env
# .env 中启用
DASHSCOPE_API_KEY=sk-your-key
```

```yaml
# 或修改 config/default.yaml
rag:
  enabled: true
  dashscope:
    api_key: ${DASHSCOPE_API_KEY}
    model: text-embedding-v3
    dimensions: 1024
  chunk_size: 500          # 切片大小（100-2000）
  chunk_overlap: 50        # 重叠大小（0-200）
  max_retrieval: 10        # 每次检索返回的最大文档数
```

---

## 记忆系统

### 短期记忆（Session Memory）

- 每个会话独立保存最近 `100` 条消息
- 自动裁剪超出上下文窗口的旧消息
- 会话切换时无缝加载历史

### 长期记忆（Long-term Memory）

- 基于 SQLite 的持久化存储
- 支持按时间、内容搜索历史对话
- 可选：将记忆条目向量化，支持语义搜索

### 数据存储

| 数据类型 | 存储位置 | 格式 |
|---|---|---|
| 会话记录 | `~/.lukawi/memory.db` | SQLite |
| 向量索引 | `~/.lukawi/chroma_db/` | ChromaDB |
| API 密钥 | 当前目录 `.env` | 纯文本 |

---

## 工具系统

### 内置工具

| 工具名称 | 功能 | 使用场景 |
|---|---|---|
| `web_fetch` | 获取网页内容 | 查询在线文档、API 参考 |
| `read_file` | 读取本地文件 | 阅读代码、配置文件 |
| `write_file` | 写入本地文件 | 生成代码、报告 |
| `list_dir` | 列出目录内容 | 浏览项目结构 |
| `edit_file` | 编辑文件内容 | 修改代码 |
| `exec_command` | 执行 Shell 命令 | 运行脚本、安装依赖 |
| `rag_search` | 搜索知识库文档 | 查询已上传的文档 |
| `rag_status` | 查看知识库状态 | 检查文档处理进度 |

### 工具安全策略

工具系统内置了安全防护机制：

- **文件访问控制**：可限制 `allowed_dirs` / `denied_dirs`
- **命令执行限制**：检测危险命令模式（如 `rm -rf /`）
- **工具策略切换**：
  - `default` — 允许所有工具
  - `restricted` — 仅允许网页抓取和文件读取，禁止命令执行和文件写入

---

## 模型切换

Lukawi 支持多模型切换，当前支持的模型：

| 模型名称 | 类型 | 说明 |
|---|---|---|
| `deepseek-v4-flash` | DeepSeek | 快速模型（默认） |
| `deepseek-v4-pro` | DeepSeek | 专业模型（更强推理能力） |
| `mock` | Mock | 测试模型（无需 API Key） |

### 切换方法

**WebUI**：点击顶栏模型名称下拉菜单切换

**命令行**：
```bash
# 查看可用模型
lukawi models

# 切换模型
lukawi models --use deepseek-v4-pro

# 启动时指定模型
lukawi webui --model deepseek-v4-pro
```

### 自定义模型

Lukawi 兼容所有 OpenAI 兼容 API。在 `config/default.yaml` 中添加：

```yaml
model:
  providers:
    my-custom-model:
      api_key: ${MY_API_KEY}
      model: my-model-name
      base_url: https://my-api-endpoint.com/v1
      max_tokens: 4096
      temperature: 0.7
```

---

## 开发指南

### 项目结构

```
lukawi-agent/
├── src/lukawi/                  # Python 源代码
│   ├── agent/                   # Agent 核心（ReAct 循环）
│   ├── cli/                     # 命令行接口（webui、chat、init 等）
│   ├── config/                  # 配置管理（加载、模型、设置）
│   ├── llm/                     # LLM 提供者（DeepSeek、Mock）
│   ├── mcp/                     # MCP 协议客户端和管理器
│   ├── memory/                  # 记忆系统（会话、长期）
│   ├── rag/                     # RAG 知识库（嵌入、存储、检索）
│   ├── server/                  # FastAPI 服务器和 SSE
│   ├── skills/                  # 技能加载和执行器
│   ├── tools/                   # 工具系统（注册、执行、策略）
│   └── utils/                   # 工具函数（日志、辅助）
├── web/                         # React + TypeScript 前端
│   ├── src/
│   │   ├── components/          # React 组件
│   │   ├── context/             # 状态管理
│   │   ├── hooks/               # 自定义 Hooks
│   │   ├── types/               # TypeScript 类型定义
│   │   └── lib/                 # 工具函数（cn、GSAP、Markdown）
│   └── vite.config.ts
├── tests/                       # 测试文件
├── config/                      # 开发和默认配置
├── skills/                      # 技能文件存储目录
├── pyproject.toml               # 项目元数据和构建配置
├── MANIFEST.in                  # 打包清单
└── .gitignore                   # Git 忽略规则
```

### 本地开发环境搭建

```bash
# 克隆仓库
git clone https://github.com/LUKAWI/lukawi-agent.git
cd lukawi-agent

# 安装开发依赖
pip install -e ".[dev]"

# 构建前端
cd web
npm install
npm run build
cd ..

# 运行测试
pytest

# 启动开发服务器
lukawi webui
```

### 测试

```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/test_agent/
pytest tests/test_rag/
pytest tests/test_tools/

# 带覆盖率
pytest --cov=src/lukawi --cov-report=html
```

### 代码规范

项目使用 `ruff` 进行代码检查和格式化：

```bash
# 代码检查
ruff check src/

# 自动修复
ruff check --fix src/

# 类型检查
mypy src/
```

---

## 常见问题

### Q: 安装后 `lukawi` 命令找不到？

Windows 用户需要确保 Python Scripts 目录在 PATH 中：
```
C:\Users\<用户名>\AppData\Roaming\Python\Python3xx\Scripts
```

或使用完整路径：
```bash
python -m lukawi webui
```

### Q: WebUI 打开后是暗色主题？

默认是亮色主题（light）。如果显示暗色，检查 `config/default.yaml` 中的 `tui.theme` 是否为 `light`。

### Q: 知识库上传文档后搜索不到？

确保已配置 `DASHSCOPE_API_KEY`，且文档格式为 `.txt`、`.md` 或 `.pdf`。查看日志确认文档是否已成功向量化。

### Q: MCP 服务器连接失败？

MCP 服务器需要 Node.js 环境。确保已安装 Node.js 18+，且 `npx` 命令可用。

### Q: 如何查看 Agent 的完整日志？

启动时添加 `--debug` 参数：
```bash
lukawi webui --debug
```

### Q: 如何更改 WebUI 端口？

设置环境变量：
```bash
# Windows PowerShell
$env:LUKAWI_PORT=8080
lukawi webui

# Linux / macOS
LUKAWI_PORT=8080 lukawi webui
```

### Q: 对话记录存储在哪里？

所有会话和记忆存储在 `~/.lukawi/memory.db`（SQLite 数据库）。删除此文件即可清除所有历史记录。

### Q: 支持哪些 LLM 提供商？

当前原生支持 DeepSeek。但 Lukawi 兼容所有 OpenAI 兼容 API，可通过修改 `config/default.yaml` 中的 `base_url` 接入其他提供商（如 OpenAI、Groq、Ollama 等）。

---

## 项目文件结构

```
lukawi-agent/
├── .gitignore                   # Git 忽略规则
├── LICENSE                      # MIT 许可证
├── MANIFEST.in                  # Python 打包清单
├── README.md                    # 双语自述文件（英文 + 中文）
├── README_CN.md                 # 本文件（详细中文文档）
├── pyproject.toml               # 项目构建和依赖配置
├── mcp-servers.example.json    # MCP 配置示例
│
├── config/                      # 配置文件目录
│   └── default.yaml             # 默认配置模板
│
├── skills/                      # 技能文件存储
│   ├── code_review/             # 代码审查技能
│   └── frontend-design/         # 前端设计技能
│
├── src/lukawi/                  # Python 后端源码
│   ├── __init__.py              # 版本号
│   ├── main.py                  # 命令行入口
│   ├── agent/                   # Agent 核心模块
│   │   ├── core.py              # ReAct 循环引擎
│   │   ├── executor.py          # 动作执行器
│   │   └── planner.py           # 规划器
│   ├── cli/                     # 命令行工具
│   │   ├── __init__.py          # AgentContext 工厂
│   │   ├── webui.py             # WebUI 启动器
│   │   ├── chat.py              # 单次对话
│   │   ├── init.py              # 初始化向导
│   │   ├── repl.py              # 终端 REPL
│   │   ├── models.py            # 模型管理
│   │   ├── config.py            # 配置管理
│   │   ├── skills.py            # 技能管理
│   │   └── status.py            # 状态查看
│   ├── commands/                # REPL 内置命令
│   │   └── builtin/             # 内置命令实现
│   ├── config/                  # 配置系统
│   │   ├── models.py            # Pydantic 配置模型
│   │   ├── settings.py          # 配置加载器
│   │   └── user_config.py       # 用户配置管理
│   ├── data/
│   │   └── default.yaml         # 打包内置默认配置
│   ├── llm/                     # LLM 集成
│   │   ├── base.py              # 抽象基类
│   │   ├── deepseek.py          # DeepSeek 提供者
│   │   ├── mock.py              # Mock 测试提供者
│   │   └── registry.py          # 模型注册表
│   ├── mcp/                     # MCP 协议
│   │   ├── client.py            # MCP 客户端
│   │   └── manager.py           # 连接管理器
│   ├── memory/                  # 记忆系统
│   │   ├── session.py           # 会话模型
│   │   ├── session_manager.py   # 会话管理器
│   │   ├── longterm.py          # 长期记忆
│   │   └── manager.py           # 记忆总控
│   ├── rag/                     # RAG 知识库
│   │   ├── embedder.py          # 嵌入模型（DashScope）
│   │   ├── store.py             # ChromaDB 向量存储
│   │   ├── retriever.py         # 检索器
│   │   ├── document.py          # 文档处理
│   │   └── manager.py           # RAG 总控
│   ├── server/                  # Web 服务
│   │   ├── app.py               # FastAPI 应用
│   │   ├── routes.py            # REST API 路由
│   │   ├── sse.py               # SSE 端点
│   │   ├── state.py             # 服务器状态
│   │   └── static/              # 前端静态资源
│   │       ├── index.html
│   │       └── assets/
│   ├── skills/                  # 技能引擎
│   │   ├── loader.py            # 技能加载器
│   │   └── executor.py          # 技能提示词生成
│   ├── tools/                   # 工具系统
│   │   ├── base.py              # 工具基类
│   │   ├── registry.py          # 工具注册表
│   │   ├── executor.py          # 工具执行器
│   │   ├── policy.py            # 工具策略
│   │   └── builtin/             # 内置工具
│   │       ├── web_fetch.py     # 网页抓取
│   │       ├── file_ops.py      # 文件操作
│   │       ├── shell.py         # Shell 命令
│   │       └── rag_search.py    # 知识库搜索
│   └── utils/                   # 工具函数
│       ├── logging.py           # 日志配置
│       └── helpers.py           # 辅助函数
│
├── tests/                       # 测试套件
│   ├── conftest.py
│   ├── test_agent/              # Agent 测试
│   ├── test_llm/                # LLM 测试
│   ├── test_mcp/                # MCP 测试
│   ├── test_memory/             # 记忆测试
│   ├── test_rag/                # RAG 测试
│   ├── test_tools/              # 工具测试
│   └── test_integration/        # 集成测试
│
├── web/                         # React + TypeScript 前端
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx             # 入口文件
│       ├── App.tsx              # 根组件
│       ├── globals.css          # 全局样式（Tailwind + CSS 变量）
│       ├── api.ts               # API 客户端
│       ├── types/
│       │   └── index.ts         # TypeScript 类型 + SSE 类型守卫
│       ├── context/
│       │   └── AppContext.tsx   # 全局状态（Context + Reducer）
│       ├── hooks/
│       │   ├── useSSE.ts        # SSE 流式 Hook
│       │   ├── useSessions.ts   # 会话管理 Hook
│       │   └── useKnowledgeUpload.ts  # 文件上传 Hook
│       ├── lib/
│       │   ├── utils.ts         # cn() 工具函数
│       │   ├── gsap.ts          # GSAP 动画辅助
│       │   └── markdown.ts      # Markdown 处理
│       └── components/
│           ├── Header.tsx        # 顶栏
│           ├── Sidebar.tsx       # 侧边栏外壳
│           ├── ChatPanel.tsx     # 聊天面板
│           ├── MessageList.tsx   # 消息列表
│           ├── InputBar.tsx      # 输入栏
│           ├── StatusBar.tsx     # 状态栏
│           ├── WelcomeScreen.tsx # 欢迎屏
│           ├── ShortcutsPanel.tsx # 快捷键面板
│           ├── Logo.tsx          # Logo 组件
│           ├── ThinkingIndicator.tsx # 思考指示器
│           └── sidebar/          # 侧边栏子组件
│               ├── index.ts
│               ├── Section.tsx
│               ├── SessionList.tsx
│               ├── ModelSelector.tsx
│               ├── SkillToggle.tsx
│               ├── McpStatus.tsx
│               └── KnowledgeBase.tsx
│
└── dist/                        # 构建输出（sdist）
    └── lukawi-0.1.3.tar.gz
```

---

## 许可证

本项目基于 [MIT License](./LICENSE) 开源。

---

<p align="center">
  <strong>Lukawi Agent</strong> — 你的本地 AI 助手
  <br>
  <a href="https://pypi.org/project/lukawi/">PyPI</a> · 
  <a href="https://github.com/LUKAWI/lukawi-agent">GitHub</a> · 
  <a href="https://github.com/LUKAWI/lukawi-agent/issues">报告问题</a>
</p>
