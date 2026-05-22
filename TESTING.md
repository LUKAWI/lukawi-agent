# Lukawi Agent 全功能测试指南

> 从单元测试到端到端，一步步验证整个系统。

---

## 快速开始

```bash
# 1. 运行所有单元测试（203 个，无需 API Key）
pytest

# 2. 端到端测试（需要 DeepSeek API Key）
$env:DEEPSEEK_API_KEY="sk-xxx"
pytest tests/test_integration/

# 3. Mock 模式启动 TUI（无需任何 Key）
lukawi --mock
```

---

## 测试层级

```
层级 1: 单元测试 ─────── pytest（203 tests） ✅ 无需任何外部依赖
    │
层级 2: 组件集成测试 ──── pytest（独立组件联动）
    │
层级 3: 端到端测试 ────── pytest + 真实 API
    │
层级 4: MCP 连通性测试 ── 测试 MCP 服务器连接
    │
层级 5: 手动 TUI 测试 ─── 启动界面实际使用
```

---

## 层级 1：单元测试（最快，先跑这个）

```bash
# 全部
pytest -v

# 分模块
pytest tests/test_config/          # 配置系统
pytest tests/test_llm/             # LLM 抽象层
pytest tests/test_tools/           # 工具系统（注册表、策略、执行器、内置工具）
pytest tests/test_agent/           # Agent 核心（ReAct 循环）
pytest tests/test_memory/          # 记忆系统
```

验证标准：**全部通过**（目前 203 passed, 4 skipped）。

---

## 层级 2：组件集成测试

验证各组件能否协同工作。

### 2.1 配置 + 模型注册表

```python
# 验证配置能加载、模型能注册切换
python -c "
from lukawi.config.settings import load_config
from lukawi.llm.registry import ModelRegistry
from lukawi.llm.mock import MockProvider

config = load_config()
registry = ModelRegistry()
registry.register('mock', MockProvider())
registry.use('mock')
print(f'Default model: {registry.current_name}')
print(f'Models: {[m.name for m in registry.list_models()]}')
print('OK: Config + Registry')
"
```

### 2.2 工具注册 + 策略过滤

```python
python -c "
from lukawi.tools.registry import ToolRegistry
from lukawi.tools.policy import ToolPolicy, PolicyContext
from lukawi.tools.builtin.web_fetch import register_web_fetch
from lukawi.config.models import ToolPolicyConfig

registry = ToolRegistry()
register_web_fetch(registry)

policy = ToolPolicy(ToolPolicyConfig())
context = PolicyContext(profile='default')

tools = registry.list_tools()
print(f'Registered: {len(tools)} tools')
filtered = policy.filter_tools(tools, context)
print(f'After policy: {len(filtered)} tools')
print('OK: Registry + Policy')
"
```

### 2.3 Mock Agent 完整循环

```python
python -c "
import asyncio
from lukawi.llm.mock import MockProvider
from lukawi.llm.base import LLMResponse
from lukawi.tools.registry import ToolRegistry
from lukawi.tools.builtin.web_fetch import register_web_fetch
from lukawi.tools.executor import ToolExecutor
from lukawi.agent.core import ReActAgent, AgentConfig, AgentEventType

async def test():
    llm = MockProvider(responses=[
        LLMResponse(content='Hello! I am Lukawi.'),
    ])
    tools = ToolRegistry()
    register_web_fetch(tools)
    agent = ReActAgent(llm=llm, tools=tools, config=AgentConfig(max_steps=3))

    async for event in agent.run('Say hello'):
        if event.type == AgentEventType.FINAL_ANSWER:
            print(f'Agent reply: {event.data[\"content\"]}')
    print('OK: Mock Agent loop')

asyncio.run(test())
"
```

---

## 层级 3：端到端测试（需要 DeepSeek API Key）

### 3.1 设置 API Key

```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-你的key"
```

### 3.2 运行端到端测试

```bash
pytest tests/test_integration/test_e2e.py -v
```

测试内容：
| 测试 | 验证什么 | 预期结果 |
|------|---------|----------|
| `test_simple_chat` | DeepSeek API 连通性 | 返回包含 "Lukawi" 的回复 |
| `test_tool_call_capability` | LLM 识别工具调用 | LLM 选择 `web_fetch` 工具 |
| `test_full_agent_reply` | 完整 ReAct 循环 | 正确回答 "4" |
| `test_streaming_chat` | 流式 API | 多个 chunk，完整文本 |

### 3.3 自定义测试脚本

```python
import asyncio
from lukawi.config.models import DeepSeekConfig
from lukawi.llm.deepseek import DeepSeekProvider
from lukawi.llm.base import Message, MessageRole

async def test():
    provider = DeepSeekProvider(DeepSeekConfig(
        api_key="sk-xxx",       # 替换为你的 key
        model="deepseek-v4-flash"
    ))

    # 简单对话
    response = await provider.chat([
        Message(role=MessageRole.USER, content="Say hello")
    ])
    print(f'Response: {response.content}')
    print(f'Tokens: {response.usage}')

    # 流式对话
    print('Stream: ', end='')
    async for chunk in provider.chat_stream([
        Message(role=MessageRole.USER, content="Count to 3")
    ]):
        if chunk.content:
            print(chunk.content, end='')
    print()

asyncio.run(test())
```

---

## 层级 4：MCP 连通性测试

测试 MCP 服务器能否启动和连接。

### 4.1 测试 Sequential Thinking

```bash
# 直接启动测试（无头模式）
echo "{}" | npx -y @modelcontextprotocol/server-sequential-thinking
# 应输出 JSON-RPC 响应
```

### 4.2 通过 Lukawi 测试 MCP 连接

```bash
# 启动并自动连接配置中的 MCP 服务器
lukawi --mock

# 在 TUI 中查看 MCP 状态
> /mcp list
```

### 4.3 单独测试 MCP 管理器

```python
import asyncio
from lukawi.mcp.client import MCPServerConfig
from lukawi.mcp.manager import MCPManager
from lukawi.tools.registry import ToolRegistry

async def test():
    registry = ToolRegistry()
    manager = MCPManager()

    # 注册内置工具
    from lukawi.tools.builtin.web_fetch import register_web_fetch
    register_web_fetch(registry)

    # 连接 sequential-thinking MCP
    config = MCPServerConfig(
        name="test-st",
        command=["npx", "-y", "@modelcontextprotocol/server-sequential-thinking"],
    )

    ok = await manager.connect_server(config, registry)
    print(f'Connected: {ok}')

    if ok:
        print(f'Total tools in registry: {registry.count}')
        for t in registry.list_tools():
            print(f'  - {t.name}: {t.description[:60]}')
        await manager.disconnect_all()

asyncio.run(test())
```

---

## 层级 5：手动 TUI 测试

### 5.1 Mock 模式启动（无需任何 Key）

```bash
lukawi --mock
```

预期：
- 标题栏显示 `Lukawi Agent`
- 底部有输入框
- 系统消息 "Welcome to Lukawi!"
- 输入消息后 AI 用模拟回复响应

### 5.2 测试所有命令

```bash
# 在 TUI 中依次输入：

/help              # 应显示所有命令列表
/clear             # 应清空聊天
/models            # 应列出可用模型（至少 mock）
/models use mock   # 应切换成功
/skill list        # 应列出 code_review 和 web_search
/skill load code_review  # 应加载成功
/skill active      # 应显示已激活的技能
/mcp list          # 应列出 MCP 服务器
/quit              # 应退出
```

### 5.3 测试工具调用

```
帮我查一下 Python 3.13 的新特性
# Mock 模式下会模拟回复，不会实际调用工具
```

### 5.4 真实模式启动（需要 API Key）

```bash
$env:DEEPSEEK_API_KEY="sk-xxx"
lukawi
```

测试对话：
```
1. "你好"                      → 应回复中文
2. "帮我查一下今天的比特币价格"  → 应调用 web_fetch 工具
3. "帮我 review 这段代码: def add(a,b): return a+b"  → 应触发 code_review 技能
```

---

## 完整测试流程（一键验证）

将以下内容保存为 `run_all_tests.py`：

```python
"""全功能一键测试脚本"""

import asyncio
import sys


def step(msg):
    print(f'\n{"="*60}')
    print(f'  {msg}')
    print(f'{"="*60}')


async def test_config():
    step('1/6: 配置加载测试')
    from lukawi.config.settings import load_config
    c = load_config()
    assert c.model.default == 'deepseek'
    assert len(c.mcp.servers) == 2
    print(f'  Model: {c.model.default}')
    print(f'  MCP servers: {[s.name for s in c.mcp.servers]}')
    print('  PASS')


async def test_llm_mock():
    step('2/6: Mock LLM 测试')
    from lukawi.llm.mock import MockProvider
    from lukawi.llm.base import Message, MessageRole
    p = MockProvider()
    r = await p.chat([Message(role=MessageRole.USER, content='Hi')])
    assert r.content is not None
    print(f'  Response: {r.content[:60]}')
    print('  PASS')


async def test_tools():
    step('3/6: 工具系统测试')
    from lukawi.tools.registry import ToolRegistry
    from lukawi.tools.builtin.web_fetch import register_web_fetch
    from lukawi.tools.builtin.file_ops import register_file_ops
    from lukawi.tools.policy import ToolPolicy, PolicyContext
    from lukawi.config.models import ToolPolicyConfig

    registry = ToolRegistry()
    register_web_fetch(registry)
    register_file_ops(registry)
    assert registry.count >= 5
    print(f'  Tools registered: {registry.count}')

    policy = ToolPolicy(ToolPolicyConfig())
    allowed = policy.filter_tools(registry.list_tools(), PolicyContext(profile='restricted'))
    print(f'  Restricted profile allows: {len(allowed)} tools')
    print('  PASS')


async def test_skills():
    step('4/6: 技能系统测试')
    from lukawi.skills.loader import SkillLoader
    from lukawi.skills.executor import match_triggers, build_skill_prompt

    loader = SkillLoader('skills')
    skills = loader.load_directory()
    assert len(skills) >= 2
    print(f'  Skills loaded: {len(skills)}')
    for s in skills:
        print(f'    - {s.name} (triggers: {s.triggers})')

    matched = match_triggers('review this code', skills)
    assert any(s.name == 'code_review' for s in matched)
    print(f'  Trigger matching works')
    print('  PASS')


async def test_agent():
    step('5/6: Agent ReAct 循环测试')
    from lukawi.llm.mock import MockProvider
    from lukawi.llm.base import LLMResponse
    from lukawi.tools.registry import ToolRegistry
    from lukawi.tools.builtin.web_fetch import register_web_fetch
    from lukawi.agent.core import ReActAgent, AgentConfig, AgentEventType

    llm = MockProvider(responses=[LLMResponse(content='Hello!')])
    tools = ToolRegistry()
    register_web_fetch(tools)
    agent = ReActAgent(llm=llm, tools=tools, config=AgentConfig(max_steps=3))

    events = [e async for e in agent.run('Hi')]
    assert any(e.type == AgentEventType.FINAL_ANSWER for e in events)
    print(f'  Events generated: {len(events)}')
    print('  PASS')


async def test_memory():
    step('6/6: 记忆系统测试')
    from lukawi.memory.manager import MemoryManager
    from lukawi.llm.base import Message, MessageRole

    manager = MemoryManager(db_path=':memory:')
    await manager.initialize()
    manager.add_message(Message(role=MessageRole.USER, content='Hello'))
    assert manager.session.message_count == 1

    mid = await manager.save_conversation(user_id='test')
    assert mid is not None
    print(f'  Memory saved: {mid[:8]}...')
    await manager.close()
    print('  PASS')


async def main():
    print(f'{"#"*60}')
    print(f'  Lukawi Agent 全功能测试')
    print(f'  Python {sys.version}')
    print(f'{"#"*60}')

    await test_config()
    await test_llm_mock()
    await test_tools()
    await test_skills()
    await test_agent()
    await test_memory()

    print(f'\n{"="*60}')
    print(f'  ✅ 全部测试通过！')
    print(f'{"="*60}')


if __name__ == '__main__':
    asyncio.run(main())
```

---

## 测试速查表

| 测试内容 | 命令 | 需要 API Key |
|----------|------|-------------|
| 单元测试（全部） | `pytest` | ❌ |
| 单元测试（分模块） | `pytest tests/test_llm/` | ❌ |
| 一键全功能脚本（无网络） | `python run_all_tests.py` | ❌ |
| 端到端（真实 API） | `pytest tests/test_integration/` | ✅ DeepSeek |
| Mock TUI | `lukawi --mock` | ❌ |
| 真实 TUI | `lukawi` | ✅ DeepSeek |
| MCP 连通性 | `npx ...sequential-thinking` | ❌ |
