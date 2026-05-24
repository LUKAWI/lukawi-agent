# Lukawi Agent

A lightweight, extensible AI Agent framework with ReAct loop, tool calling, memory, and knowledge base.

## Features

- **ReAct Loop Agent** — reasoning + acting with automatic tool calling
- **Streaming Chat** — token-by-token real-time output in WebUI
- **Tool System** — built-in tools: web fetch, file operations, shell commands
- **Extensible Skills** — drop `SKILL.md` files to teach the agent new abilities
- **MCP Protocol** — connect external tool servers (sequential thinking, code context, etc.)
- **Memory** — session-based short-term + persistent long-term memory with search
- **RAG Knowledge Base** — upload documents, semantic search via DashScope embeddings
- **WebUI** — React-based chat interface with model switching, session management
- **TUI** — terminal-based interactive REPL with Rich formatting

## Quick Start

### 1. Install

```bash
pip install lukawi
```

### 2. Initialize

```bash
lukawi-init
```

This interactive wizard will ask for:
- **DeepSeek API Key** (required for LLM)
- **DashScope API Key** (optional, for RAG / knowledge base)
- **MCP Servers** (optional, for extra tools)

### 3. Launch

```bash
# Web UI (recommended)
lukawi webui

# Terminal REPL
lukawi
```

Open http://localhost:50109 in your browser.

### 4. Add Skills (optional)

Drop `SKILL.md` files into the `skills/` directory:

```
skills/
├── my-skill/
│   └── SKILL.md
```

## Configuration

All configuration is read from `config/default.yaml`. Override via environment variables or a `.env` file:

```env
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DASHSCOPE_API_KEY=sk-...
```

MCP servers are configured in `~/.lukawi/mcp-servers.json`.

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+B` | Toggle sidebar |
| `Ctrl+L` | Clear chat |
| `Enter` | Send message |
| `Shift` + `Enter` | New line |
| `/` | Command mode |

## Development

```bash
git clone https://github.com/lukawi-team/lukawi.git
cd lukawi
pip install -e ".[dev]"

# Run tests
pytest

# Build frontend
cd web && npm install && npm run build
```

## License

MIT
