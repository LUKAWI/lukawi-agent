# Lukawi Agent 用户手册

> 看不懂说明书？没关系，从这里开始，一步一步来。

---

## 📋 目录

1. [这是什么？](#1-这是什么)
2. [安装](#2-安装)
3. [快速启动](#3-快速启动)
4. [TUI 界面介绍](#4-tui-界面介绍)
5. [所有快捷键](#5-所有快捷键)
6. [所有命令](#6-所有命令)
7. [工具调用](#7-工具调用)
8. [更换模型](#8-更换模型)
9. [配置文件详解](#9-配置文件详解)
10. [常见问题](#10-常见问题)

---

## 1. 这是什么？

**Lukawi** 是一个 AI 助手，它能：

- ✅ 理解你问的问题
- ✅ **自己决定要不要用工具**（比如上网查资料、读文件、执行命令）
- ✅ 调用工具拿到结果，再整理好告诉你
- ✅ 多轮对话，记得住上下文

**简单说**：像 ChatGPT 但多了"手"——它能自己动手做事。

---

## 2. 安装

### 2.1 准备工作

你需要：
- **Python 3.10 或更高版本**
- 一个 **DeepSeek API Key**（如果没有，可以去 [platform.deepseek.com](https://platform.deepseek.com) 注册）

> 💡 **不想花钱？** 可以用 `--mock` 模式，不需要 API Key，但只能看到模拟回复。

### 2.2 安装 Lukawi

打开终端（cmd 或 PowerShell），执行：

```bash
pip install lukawi
```

### 2.3 配置 API Key

**方法一：环境变量（推荐）**

```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-你的key"

# 或者永久设置（管理员 PowerShell）
[System.Environment]::SetEnvironmentVariable('DEEPSEEK_API_KEY', 'sk-你的key', 'User')
```

**方法二：配置文件**

在 `config/default.yaml` 中找到这一行，替换成你的 key：

```yaml
api_key: sk-你的key
```

---

## 3. 快速启动

### 3.1 启动 TUI（图形界面）

```bash
lukawi
```

看到这个画面就说明成功了：
```
┌────────────────────────────────────────────┐
│  Lukawi Agent                             │
├────────────────────────────────────────────┤
│                                            │
│  ⚙️ Welcome to Lukawi!                     │
│  Type a message or /help for commands.    │
│                                            │
├────────────────────────────────────────────┤
│  >                                         │
└────────────────────────────────────────────┘
```

### 3.2 第一次对话

在底部的输入框输入：

```
你好，请介绍一下你自己
```

按 `Enter` 发送，Lukawi 就会回复你。

### 3.3 用 Mock 模式试试（不需要 API Key）

```bash
lukawi --mock
```

这个模式下所有回复都是模拟的，适合测试。

---

## 4. TUI 界面介绍

```
┌──────────────────────────────────────────────┐
│  Lukawi Agent                    ⚙️ v0.1.0   │  ← 标题栏
├──────────────────────────────────────────────┤
│                                              │
│  ⚙️ Welcome to Lukawi!                       │
│                                              │  ← 聊天区
│  👤 You: 今天天气怎么样？                     │
│  🔧 Using tool: web_fetch...                 │
│  🤖 Assistant: 北京的天气是...               │
│                                              │
├──────────────────────────────────────────────┤
│  > 输入消息或 /命令...                        │  ← 输入区
├──────────────────────────────────────────────┤
│  Ctrl+C 退出  Ctrl+L 清屏  Ctrl+M 切换模型    │  ← 底部状态栏
└──────────────────────────────────────────────┘
```

**消息类型**：

| 图标 | 角色 | 说明 |
|------|------|------|
| 👤 **You** | 用户 | 你发送的消息 |
| 🤖 **Assistant** | 助手 | AI 的回复 |
| ⚙️ **System** | 系统 | 提示信息和命令结果 |
| 🔧 **Tool** | 工具 | 表示正在使用工具 |
| ❌ **Error** | 错误 | 出错信息 |

---

## 5. 所有快捷键

| 快捷键 | 作用 |
|--------|------|
| `Enter` | 发送消息 |
| `Ctrl+C` | 退出程序 |
| `Ctrl+L` | 清空聊天记录 |
| `Ctrl+M` | 显示可用模型列表 |

---

## 6. 所有命令

在输入框输入命令（以 `/` 开头）：

### `/help`
显示帮助信息。

```
> /help
```

### `/clear`
清空聊天记录。

```
> /clear
```

### `/models`
显示所有可用的模型。

```
> /models
```

输出示例：
```
**Available Models:**
- [✓] deepseek (deepseek)
- [ ] deepseek-pro (deepseek)
- [ ] mock (mock)
```

### `/models use <名称>`
切换到指定模型。

```
> /models use deepseek-pro
```

### `/quit`
退出程序。也可以用 `Ctrl+C`。

```
> /quit
```

---

## 7. 工具调用

这是 Lukawi **最核心的功能**——AI 可以自己决定使用哪些工具来完成任务。

### 7.1 内置工具

Lukawi 自带以下工具：

| 工具名称 | 作用 | 示例用法 |
|----------|------|----------|
| `web_fetch` | 获取网页内容 | "查一下今天的比特币价格" |
| `read_file` | 读取文件 | "帮我看一下 test.txt 的内容" |
| `write_file` | 写入文件 | "帮我保存这段代码到 app.py" |
| `edit_file` | 编辑文件 | "把文件中的 'hello' 改成 'world'" |
| `list_dir` | 列出目录 | "看看当前文件夹有什么文件" |
| `exec_command` | 执行命令 | "帮我看看 Python 版本" |

### 7.2 实际场景举例

**场景一：上网查资料**

```
你：帮我查一下 Python 3.13 有什么新特性
```

Lukawi 会：
1. 🤔 "用户想知道 Python 3.13 的新特性，我用 web_fetch 去查"
2. 🔧 调用 `web_fetch(url="https://docs.python.org/3/whatsnew/3.13.html")`
3. 🤖 "Python 3.13 的主要新特性包括：更好的错误提示、改进的交互式解释器..."

**场景二：读写文件**

```
你：帮我创建一个 todo.txt 文件
```

Lukawi 会：
1. 🤔 "用户要创建文件，我用 write_file"
2. 🔧 调用 `write_file(path="todo.txt", content="1. 学习 Python\n2. 写代码")`
3. 🤖 "文件已创建，写入了 2 行待办事项"

**场景三：执行命令**

```
你：帮我看看当前目录有什么文件
```

Lukawi 会：
1. 🤔 "用户想看目录内容，我用 list_dir"
2. 🔧 调用 `list_dir(path=".")`
3. 🤖 "当前目录下有：README.md, src/, tests/, ..."

### 7.3 工具调用是怎么工作的？

Lukawi 的 "思考-行动-观察" 循环：

```
你提问
  │
  ▼
┌─ 思考 ─────────────────────────┐
│  AI 分析你的问题，决定用哪个    │
│  工具，以及传什么参数           │
└───────────┬────────────────────┘
            │
            ▼
┌─ 行动 ─────────────────────────┐
│  调用工具，获取结果             │
│  （比如上网查数据）             │
└───────────┬────────────────────┘
            │
            ▼
┌─ 观察 ─────────────────────────┐
│  把工具结果给 AI 分析           │
│  AI 决定是继续用工具还是直接回  │
│  答                             │
└───────────┬────────────────────┘
            │
    ┌───────┴───────┐
    ▼               ▼
  继续用工具       直接回答
  （回到思考）     （输出结果）
```

整个过程是自动的，你只需要正常提问就行。

### 7.4 工具安全策略

Lukawi 有内置的安全机制：

- 🛡️ **危险命令拦截**：像 `rm -rf /` 这种命令会被自动拦截
- 🛡️ **配置文件限制**：可以通过 `config/default.yaml` 配置哪些工具能用
- 🛡️ **超时保护**：每个工具有默认 30 秒超时，防止卡住

---

## 8. 更换模型

### 8.1 配置多个模型

在 `config/default.yaml` 中：

```yaml
model:
  default: deepseek
  providers:
    deepseek:
      api_key: ${DEEPSEEK_API_KEY}
      model: deepseek-v4-flash
      max_tokens: 4096
      temperature: 0.7
    
    deepseek-pro:
      api_key: ${DEEPSEEK_API_KEY}
      model: deepseek-v4-pro
      temperature: 0.5
    
    mock:
      type: mock
```

### 8.2 运行时切换

方法一 — 在 TUI 中：

```
> /models                 # 查看所有模型
> /models use deepseek-pro  # 切换到 pro 模型
```

方法二 — 启动时指定：

```bash
lukawi --model deepseek-pro
```

### 8.3 使用 Mock 模式

不需要 API Key，适合测试：

```bash
lukawi --mock
```

---

## 9. 配置文件详解

配置文件位于 `config/default.yaml`，或者用 `--config` 指定：

```bash
lukawi --config my-config.yaml
```

### 完整配置项

```yaml
# ========== 模型设置 ==========
model:
  default: deepseek                           # 默认模型
  providers:
    deepseek:
      api_key: ${DEEPSEEK_API_KEY}            # API Key（支持环境变量）
      model: deepseek-v4-flash                # 模型名
      base_url: https://api.deepseek.com      # API 地址
      max_tokens: 4096                        # 最大返回 token 数
      temperature: 0.7                        # 随机性 (0-2)

# ========== 工具权限 ==========
tools:
  default_profile: default                    # 默认权限配置
  profiles:
    default:                                  # 默认配置：所有工具可用
      allowed_tools: ["*"]
      denied_tools: []
    restricted:                              # 受限配置：只能读不能写
      allowed_tools: [web_fetch, read_file, list_dir]
      denied_tools: [exec_command, write_file, edit_file]

# ========== Agent 行为 ==========
agent:
  max_steps: 10                              # 单次对话最大思考步数
  max_tokens: 100000                         # 总 token 上限
  loop_detection: true                       # 是否检测死循环
  loop_threshold: 3                          # 相同工具调用 3 次视为循环

# ========== 记忆系统 ==========
memory:
  enabled: true                              # 是否启用记忆
  session:
    max_messages: 100                        # 会话最多保留 100 条消息
  longterm:
    enabled: true                            # 是否启用长期记忆
    db_path: memory.db                       # 记忆数据库文件

# ========== 日志 ==========
logging:
  level: INFO                                # 日志级别
  rich: true                                 # 是否彩色日志
```

### 环境变量

| 变量名 | 作用 | 示例 |
|--------|------|------|
| `DEEPSEEK_API_KEY` | API 密钥 | `sk-xxx` |
| `LUKAWI_LOG_LEVEL` | 日志级别 | `DEBUG` |

---

## 10. 连接 MCP 服务器

MCP (Model Context Protocol) 可以让 Lukawi 连接外部服务器，获得更多工具能力。

### 10.1 配置 MCP 服务器

在 `config/default.yaml` 的 `mcp.servers` 段添加：

```yaml
mcp:
  servers:
    # 文件系统服务器：让 AI 能读写指定目录
    - name: fs
      command: ["npx", "-y", "@modelcontextprotocol/server-filesystem"]
      args: ["C:/path/to/allowed/directory"]

    # SQLite 数据库服务器：让 AI 能查数据库
    - name: db
      command: ["npx", "-y", "@modelcontextprotocol/server-sqlite"]
      args: ["C:/path/to/database.db"]
```

### 10.2 启动时自动加载

```bash
# 正常启动（自动从 config 加载 MCP 服务器）
lukawi

# 指定独立的 MCP 配置文件
lukawi --mcp my-mcp-servers.yaml
```

### 10.3 工具自动注册

Lukawi 启动时会：
1. 连接所有配置的 MCP 服务器
2. 自动发现每个服务器提供的工具
3. 注册到 ToolRegistry，和内置工具一样使用
4. LLM 会自动选择使用 MCP 工具

```
AI 思考 → "用户要操作文件系统，我有 fs_list_directory 工具"
AI 行动 → MCPClient.call_tool("fs_list_directory", ...)
                                    ↓
                         MCP 服务器 (/filesystem)
                                    ↓
                         返回目录列表
AI 回答 → "当前目录下有：..."
```

### 10.4 MCP 工作原理

```
Lukawi Agent
    │
    ├── ToolRegistry
    │       ├── web_fetch          ← 内置工具
    │       ├── read_file          ← 内置工具
    │       ├── exec_command       ← 内置工具
    │       ├── fs_list_directory  ← MCP 注册的
    │       ├── fs_read_file       ← MCP 注册的
    │       └── db_query           ← MCP 注册的
    │
    └── MCPManager
            ├── MCPClient("fs") → 子进程 (stdio JSON-RPC)
            └── MCPClient("db") → 子进程 (stdio JSON-RPC)
```

### 10.5 启动时自动清理

退出程序时，Lukawi 会自动断开所有 MCP 服务器连接。

---

## 11. 技能系统 (Skills)

Lukawi 的技能系统支持**两种调用模式**，和 OpenCode 一致。

Skills 是**技能包**——用 SKILL.md 文件写的一组指令，告诉 AI 怎么完成特定类型的任务。

### 11.1 两种调用模式

| 模式 | 触发方式 | 示例 |
|------|----------|------|
| **显式调用** | 在 TUI 输入 `/skill load <名称>` | `/skill load code_review` |
| **隐式调用** | 用户消息匹配到 SKILL.md 中定义的 `triggers` 关键词 | 输入"帮我**找**一下 Python 教程"自动触发 `web_search` |

**隐式调用的工作流程**：
```
用户输入: "帮我 review 一下这段代码"
                    │
                    ▼
    match_triggers("帮我 review 一下这段代码", skills)
                    │
                    ▼
    "review" 匹配 → code_review 技能 → inject_system_message()
                    │
                    ▼
    后续 AI 回复时会看到 code_review 的指令
```

### 11.2 编写一个 Skill（带触发词）

|            | 工具 (Tools)               | 技能 (Skills)             |
|------------|---------------------------|--------------------------|
| 本质       | 可执行的函数              | 一段文字指令              |
| 谁执行     | AI 调用，代码执行         | AI 自己按说明做           |
| 例子       | `web_fetch` 真的去请求网页 | "搜索教程"教你怎么一步步搜 |

### 11.2 编写一个 Skill

在 `skills/` 目录下创建文件夹和 `SKILL.md`。`triggers` 字段定义关键词，用户消息匹配时会**自动加载**：

```markdown
---
name: code_review
description: Review code for bugs, security issues, and style problems
triggers:               # ← 隐式触发的关键词
  - review
  - code review
  - check my code
  - is this code
---

# Code Review Skill

When asked to review code:

1. Check for security vulnerabilities
2. Check for performance issues
3. Check code style and readability
4. Provide specific suggestions
```

### 11.3 TUI 命令管理技能

| 命令 | 作用 |
|------|------|
| `/skill list` | 列出所有可用技能（含触发词） |
| `/skill load <名称>` | 显式加载某个技能（全量指令注入） |
| `/skill active` | 查看当前已激活的技能 |

### 11.4 启动时加载

```bash
lukawi                          # 自动扫描 skills/ 下所有 SKILL.md
lukawi --skills-dir ./my-skills # 指定目录
```

### 11.5 隐式触发 vs 显式加载

**隐式触发**：用户消息中的关键词自动匹配技能
```
你: "帮我 review 一下这段代码"
    → 触发词 "review" 匹配 code_review 技能
    → 技能指令注入 AI 上下文
    → AI 按 code_review 的方式回复
```

**显式加载**：手动指定技能
```
> /skill load code_review
    → "Skill 'code_review' loaded"
    → 后续 AI 消息都包含该技能的完整指令
```

### 11.6 SKILL.md 触发词定义

```markdown
---
name: web_search
description: 搜索网络信息
triggers:        # 匹配这些词的任意一个就自动加载
  - search
  - find
  - look up
  - what is
  - tell me about
---
```

触发词匹配是**大小写不敏感**的，任意一个出现在用户消息中就会触发。

### 11.7 已有的示例技能

```
skills/
  ├── web_search/SKILL.md      # 网络搜索 (triggers: search, find, look up...)
  └── code_review/SKILL.md     # 代码审查 (triggers: review, code review...)
```

---

## 12. 完整调用链路

以下是 Lukawi 从收到消息到回复的完整处理流程：

```
┌─────────────────────────────────────────────────────────────────┐
│  用户输入: "帮我查一下 Python 3.13 的新特性"                     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────── TUI ─────────────────┐
│  lukawi/tui/app.py                    │
│  _process_message("...")              │
└───────────────────────────────────────┘
                                │
                                ▼
┌───────────────── Agent Core (ReAct Loop) ─────────────────┐
│  lukawi/agent/core.py                                     │
│                                                           │
│  1. _think() ─── 构建 system prompt (含 skills)            │
│       │            + 工具 schema (含 MCP 工具)              │
│       │            ↓                                      │
│       │          LLM 返回: {"tool": "web_fetch", ...}      │
│       │                                                   │
│  2. _act() ───── 从 ToolRegistry 查找工具                  │
│       │            ├── 内置工具 → 直接执行                  │
│       │            └── MCP 工具 → MCPManager → MCPClient  │
│       │            ↓                                      │
│       │          返回 ToolResult                           │
│       │                                                   │
│  3. _observe() ─ 把工具结果加回对话历史                      │
│       │                                                   │
│  4. 回到第1步，直到 LLM 直接回答不再调工具                     │
└───────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────── Output ─────────────────┐
│  AI 回复: "Python 3.13 的新特性包括..."   │
└──────────────────────────────────────────┘
```

### 配置加载链路

```
lukawi --config my.yaml --model pro --mock
    │
    ├── config/settings.py → AppConfig (模型/工具/记忆/MCP/Skills)
    ├── ModelRegistry → DeepSeekProvider / MockProvider
    ├── ToolRegistry → web_fetch, file_ops, shell + MCP 工具
    ├── MCPManager → 连接服务器 → 注册工具
    ├── SkillLoader → 加载 SKILL.md → 注入 system prompt
    └── ReActAgent → 整合所有组件
```

---

## 13. 常见问题

### Q: 启动后黑屏 / 闪退？
**A**: 检查 Python 版本 `python --version`，需要 3.10+。也可能是 API Key 没配好，先用 `lukawi --mock` 试试。

### Q: AI 不调用工具，直接回答？
**A**: 有些简单问题 AI 觉得不需要工具。你可以明确说"帮我查一下..."或"帮我搜索..."来提示它。

### Q: 工具调用卡住了 / 超时？
**A**: 网络问题可能导致 web_fetch 超时。可以重试。shell 命令如果执行太久也会超时（默认 30 秒）。

### Q: 怎么换一个模型？
**A**: 在 TUI 里输入 `/models use 模型名`，或者在启动时加 `--model 模型名`。

### Q: 我想限制 AI 不能用某个工具？
**A**: 修改 `config/default.yaml`，把要限制的工具加到 `denied_tools` 列表里。

### Q: 命令执行被拦截了？
**A**: 安全策略会拦截危险命令（如 `rm -rf /`）。如果你需要执行，可以在配置文件中修改 `dangerous_patterns` 列表。但请确保你知道自己在做什么！

### Q: 怎么退出？
**A**: 按 `Ctrl+C` 或输入 `/quit`。

### Q: 怎么清屏？
**A**: 按 `Ctrl+L` 或输入 `/clear`。

---

> 有问题？查阅 `CLAUDE.md`（开发文档）或 `DEVELOPMENT_SPEC.md`（技术规范）。
>
> 祝你使用愉快！🎉
