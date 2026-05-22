# Lukawi Agent Framework

> A lightweight AI Agent framework with ReAct loop, tool calling, and memory

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🤖 **ReAct Loop**: Think → Act → Observe cycle for complex reasoning
- 🔧 **Tool Calling**: Extensible tool system with policy pipeline
- 💾 **Memory System**: Session and long-term memory with SQLite
- 🖥️ **TUI Interface**: Beautiful terminal UI with Textual
- 🔌 **DeepSeek Integration**: Native support for DeepSeek API
- 🔀 **Model Switching**: Easy model switching at runtime
- 🛡️ **Tool Policies**: Fine-grained tool access control
- 🪝 **Hook System**: Pre/post execution hooks for auditing

## Quick Start

### 一键安装（推荐）

```bash
# 下载后，双击运行 install.bat
# 或者命令行运行：
.\install.bat
```

`install.bat` 会自动完成安装 + PATH 配置，**重启终端后直接可用**。

### 手动安装

```bash
pip install -e .
```

如果 `lukawi` 找不到，用 `python -m lukawi.main` 代替。

### 启动

```bash
# 零配置体验（Mock 模式，无需 API Key）
lukawi --mock

# 完整模式（需要 DeepSeek API Key）
$env:DEEPSEEK_API_KEY="sk-你的key"
lukawi
```

### 获取 DeepSeek API Key

去 [platform.deepseek.com](https://platform.deepseek.com) 注册即可获得。
    deepseek:
      api_key: ${DEEPSEEK_API_KEY}
      model: deepseek-v4-flash
```

### Usage

```bash
# Start the TUI
lukawi

# Or with custom config
lukawi --config path/to/config.yaml

# Use a specific model
lukawi --model deepseek-pro
```

## TUI Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help message |
| `/clear` | Clear chat history |
| `/models` | List available models |
| `/models use <name>` | Switch to a model |
| `/models info` | Show current model info |
| `/memory` | Show memory stats |
| `/memory search <query>` | Search long-term memory |
| `/quit` | Exit the application |

## Configuration

### Model Configuration

```yaml
model:
  default: deepseek
  providers:
    deepseek:
      api_key: ${DEEPSEEK_API_KEY}
      model: deepseek-v4-flash
      base_url: https://api.deepseek.com
      max_tokens: 4096
      temperature: 0.7
    mock:
      # Mock provider for testing
      type: mock
```

### Tool Policy

```yaml
tools:
  default_profile: default
  profiles:
    default:
      allowed_tools: ["*"]
      denied_tools: []
    restricted:
      allowed_tools: ["web_fetch", "read_file"]
      denied_tools: ["exec_command"]
```

### Memory Configuration

```yaml
memory:
  enabled: true
  db_path: memory.db
  session_max_messages: 100
  longterm_enabled: true
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    TUI Layer (Textual)                   │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  Agent Core (ReAct Loop)                 │
│              Think → Act → Observe → Repeat             │
└─────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────────┐
│   LLM Layer   │  │  Tool System  │  │   Memory System   │
│   (DeepSeek)  │  │   (Registry)  │  │   (SQLite)        │
└───────────────┘  └───────────────┘  └───────────────────┘
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/lukawi-agent.git
cd lukawi-agent

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=lukawi

# Run specific tests
pytest tests/test_tools/
```

### Code Quality

```bash
# Lint
ruff check .

# Format
ruff format .

# Type check
mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.
