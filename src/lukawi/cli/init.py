"""lukawi-init — First-run setup wizard for Lukawi Agent."""

from __future__ import annotations

import json
import sys
from pathlib import Path

CONFIG_DIR = Path.home() / ".lukawi"
MCP_CONFIG = CONFIG_DIR / "mcp-servers.json"
ENV_FILE = Path.cwd() / ".env"

PRESET_MCP = [
    {
        "name": "sequential-thinking",
        "command": ["npx", "-y", "@modelcontextprotocol/server-sequential-thinking"],
        "args": [],
        "env": {},
        "desc_en": "Break down complex problems into step-by-step reasoning",
        "desc_zh": "将复杂问题拆解为逐步推理",
    },
    {
        "name": "context7",
        "command": ["npx", "-y", "@upstash/context7-mcp"],
        "args": [],
        "env": {},
        "desc_en": "Provide up-to-date library documentation and code context",
        "desc_zh": "提供最新的第三方库文档和代码上下文",
    },
    {
        "name": "tavily",
        "command": ["npx", "-y", "tavily-mcp@0.2.0"],
        "args": [],
        "env": {},
        "desc_en": "Real-time web search via Tavily API (requires TAVILY_API_KEY)",
        "desc_zh": "通过 Tavily API 进行实时网络搜索（需要 TAVILY_API_KEY）",
    },
]

T = {}  # translations — set after language selection

TEXTS = {
    "en": {
        "banner_title": "Lukawi Agent — Setup Wizard",
        "intro_1": "This wizard will help you configure Lukawi Agent for first use.",
        "intro_2": "API keys are stored in a .env file in the current directory.",
        "intro_3": "They are NEVER sent anywhere except to the API providers you configure.",
        "lang_prompt": "Choose language / 选择语言 (en/zh)",
        "step1_title": "Step 1: LLM Provider (Required)",
        "step1_desc1": "Lukawi supports any OpenAI-compatible API.",
        "step1_desc2": "At minimum you need one API key.",
        "deepseek_key_prompt": "DeepSeek API Key (for deepseek-chat / deepseek-reasoner)",
        "deepseek_url_prompt": "DeepSeek Base URL",
        "skipped_deepseek": "⚠ Skipped — DeepSeek will not be available.",
        "existing_key_hint": "  (existing key shown, press Enter to keep)",
        "step2_title": "Step 2: RAG / Knowledge Base (Optional)",
        "step2_desc1": "Enable document upload and semantic search.",
        "step2_desc2": "Requires a DashScope API key (Alibaba Cloud).",
        "dashscope_key_prompt": "DashScope API Key (leave empty to disable RAG)",
        "rag_disabled": "RAG disabled — you can enable it later by setting DASHSCOPE_API_KEY.",
        "step3_title": "Step 3: MCP Servers (Optional)",
        "step3_desc1": "MCP servers extend the agent with extra tools.",
        "step3_intro": "Select servers with Space, confirm with Enter, skip with Esc:",
        "mcp_label_selected": "[✓]",
        "mcp_label_empty": "[ ]",
        "mcp_add_custom": "Add a custom MCP server",
        "mcp_custom_name": "  Name",
        "mcp_custom_command": "  Command",
        "mcp_custom_args": "  Args (space-separated, optional)",
        "mcp_custom_added": "  ✓ Added",
        "tavily_key_prompt": "Tavily API Key (for web search, get it at https://app.tavily.com)",
        "tavily_key_skipped": "⚠ Tavily selected but no API key provided — MCP will not connect.",
        "save_title": "Saving configuration...",
        "wrote_env": "✓ Wrote",
        "wrote_mcp": "✓ Wrote",
        "wrote_mcp_empty": "✓ Wrote {path} (empty)",
        "no_keys": "No API keys configured — you can add them later in .env",
        "done_title": "Setup complete!",
        "next_1": "1. Start the Web UI:",
        "next_2": "2. Or start the terminal chat:",
        "next_3": "3. Add skills: drop SKILL.md files into skills/",
        "next_3_detail": "(see skills/ directory for examples)",
        "config_files": "Configuration files:",
        "rerun": "Re-run lukawi-init anytime to update your settings.",
    },
    "zh": {
        "banner_title": "Lukawi Agent — 安装向导",
        "intro_1": "此向导将帮助您完成 Lukawi Agent 的首次配置。",
        "intro_2": "API 密钥将保存在当前目录的 .env 文件中。",
        "intro_3": "密钥仅发送给您配置的 API 服务商，不会泄露给任何第三方。",
        "lang_prompt": "Choose language / 选择语言 (en/zh)",
        "step1_title": "步骤 1：LLM 模型提供商（必填）",
        "step1_desc1": "Lukawi 兼容所有 OpenAI 格式的 API。",
        "step1_desc2": "至少需要一个 API 密钥。",
        "deepseek_key_prompt": "DeepSeek API 密钥（用于 deepseek-chat / deepseek-reasoner）",
        "deepseek_url_prompt": "DeepSeek Base URL",
        "skipped_deepseek": "⚠ 已跳过 — DeepSeek 将不可用。",
        "existing_key_hint": "  （显示已有密钥，按 Enter 保留）",
        "step2_title": "步骤 2：RAG 知识库（可选）",
        "step2_desc1": "启用文档上传和语义搜索。",
        "step2_desc2": "需要阿里云 DashScope API 密钥。",
        "dashscope_key_prompt": "DashScope API 密钥（留空则禁用 RAG）",
        "rag_disabled": "RAG 已禁用 — 您可稍后设置 DASHSCOPE_API_KEY 来启用。",
        "step3_title": "步骤 3：MCP 服务器（可选）",
        "step3_desc1": "MCP 服务器为 Agent 提供额外的工具能力。",
        "step3_intro": "Space 选中 / 取消，Enter 确认，Esc 跳过：",
        "mcp_label_selected": "[✓]",
        "mcp_label_empty": "[ ]",
        "mcp_add_custom": "添加自定义 MCP 服务器",
        "mcp_custom_name": "  名称",
        "mcp_custom_command": "  命令",
        "mcp_custom_args": "  参数（空格分隔，可选）",
        "mcp_custom_added": "  ✓ 已添加",
        "tavily_key_prompt": "Tavily API 密钥（用于联网搜索，获取地址：https://app.tavily.com）",
        "tavily_key_skipped": "⚠ 已选择 Tavily 但未提供 API 密钥 — MCP 将无法连接。",
        "save_title": "正在保存配置...",
        "wrote_env": "✓ 已写入",
        "wrote_mcp": "✓ 已写入",
        "wrote_mcp_empty": "✓ 已写入 {path}（空）",
        "no_keys": "未配置 API 密钥 — 您可稍后在 .env 文件中添加",
        "done_title": "配置完成！",
        "next_1": "1. 启动 Web 界面：",
        "next_2": "2. 或启动终端对话：",
        "next_3": "3. 添加技能：将 SKILL.md 文件放入 skills/ 目录",
        "next_3_detail": "（参考 skills/ 目录中的示例）",
        "config_files": "配置文件：",
        "rerun": "随时重新运行 lukawi-init 来修改设置。",
    },
}


def _t(key: str) -> str:
    return T.get(key, key)


def _getch() -> str:
    if sys.platform == "win32":
        import msvcrt
        ch = msvcrt.getwch()
        if ch == "\x00" or ch == "\xe0":
            ch = msvcrt.getwch()
            return {"H": "up", "P": "down", "K": "left", "M": "right"}.get(ch, ch)
        if ch == "\r":
            return "enter"
        if ch == "\x1b":
            return "escape"
        if ch == " ":
            return "space"
        if ch == "\x08":
            return "backspace"
        if ch == "\x03":
            raise KeyboardInterrupt
        return ch
    else:
        import termios
        import tty
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                seq = sys.stdin.read(2)
                if seq == "[A":
                    return "up"
                elif seq == "[B":
                    return "down"
                elif seq == "[C":
                    return "right"
                elif seq == "[D":
                    return "left"
                return "escape"
            if ch == "\r":
                return "enter"
            if ch == " ":
                return "space"
            if ch in ("\x7f", "\x08"):
                return "backspace"
            if ch == "\x03":
                raise KeyboardInterrupt
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _prompt(prompt_text: str, default: str = "", secret: bool = False) -> str:
    if default:
        display = f"{prompt_text} [{default}]: "
    else:
        display = f"{prompt_text}: "

    if not secret:
        return input(display).strip() or default

    sys.stdout.write(display)
    sys.stdout.flush()
    value = ""

    if sys.platform == "win32":
        import msvcrt
        while True:
            ch = msvcrt.getwch()
            if ch in ("\r", "\n"):
                sys.stdout.write("\n")
                break
            elif ch == "\x08":
                if value:
                    value = value[:-1]
                    sys.stdout.write("\b \b")
            elif ch == "\x1b":
                sys.stdout.write("\n")
                return ""
            elif ch == "\x03":
                raise KeyboardInterrupt
            elif ch  and len(ch) == 1 and ord(ch) >= 32:
                value += ch
                sys.stdout.write("*")
        return value.strip() or default
    else:
        import termios
        import tty
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1)
                if ch in ("\r", "\n"):
                    sys.stdout.write("\n")
                    break
                elif ch in ("\x7f", "\x08"):
                    if value:
                        value = value[:-1]
                        sys.stdout.write("\b \b")
                elif ch == "\x1b":
                    sys.stdout.write("\n")
                    return ""
                elif ch == "\x03":
                    raise KeyboardInterrupt
                elif ch and len(ch) == 1 and ord(ch) >= 32:
                    value += ch
                    sys.stdout.write("*")
            return value.strip() or default
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _redraw_mcp(options, cursor, selected):
    for i, opt in enumerate(options):
        prefix = " >" if i == cursor else "  "
        mark = _t("mcp_label_selected") if selected[i] else _t("mcp_label_empty")
        desc = opt.get("desc_" + ("zh" if T is TEXTS["zh"] else "en"), "")
        line = f"{prefix} {mark} {opt['name']}"
        if desc:
            line += f"  —  {desc}"
        sys.stdout.write("\x1b[2K" + line + "\r\n")
    prefix = " >" if cursor == len(options) else "  "
    sys.stdout.write(f"\x1b[2K{prefix}    {_t('mcp_add_custom')}...\r\n")


def _multi_select(options) -> tuple[list[int], bool]:
    selected = [False] * len(options)
    cursor = 0
    n = len(options)
    sys.stdout.write("\x1b[?25l")
    sys.stdout.flush()
    try:
        _redraw_mcp(options, cursor, selected)
        while True:
            sys.stdout.write(f"\x1b[{n + 2}A")
            sys.stdout.flush()
            _redraw_mcp(options, cursor, selected)
            ch = _getch()
            if ch == "up":
                cursor = (cursor - 1) % (n + 1)
            elif ch == "down":
                cursor = (cursor + 1) % (n + 1)
            elif ch == "space":
                if cursor < n:
                    selected[cursor] = not selected[cursor]
                else:
                    add_custom = _prompt_custom_mcp()
                    if add_custom:
                        return [add_custom], True
            elif ch == "enter":
                if cursor < n:
                    return [i for i, s in enumerate(selected) if s], False
                else:
                    add_custom = _prompt_custom_mcp()
                    if add_custom:
                        return [add_custom], True
                    return [i for i, s in enumerate(selected) if s], False
            elif ch == "escape":
                return [], False
    finally:
        sys.stdout.write("\x1b[?25h")
        sys.stdout.flush()


def _prompt_custom_mcp():
    sys.stdout.write("\x1b[2K\r")
    sys.stdout.flush()
    name = _prompt(_t("mcp_custom_name"))
    if not name:
        print("")
        return None
    cmd = _prompt(_t("mcp_custom_command"))
    if not cmd:
        print("")
        return None
    args = _prompt(_t("mcp_custom_args"))
    print(f"  {_t('mcp_custom_added')} '{name}'")
    print()
    return {"name": name, "command": cmd.split(), "args": args.split() if args else [], "env": {}}


def main() -> None:
    global T

    print()
    print("╔══════════════════════════════════════════╗")
    print("║       Lukawi Agent — Setup Wizard       ║")
    print("╚══════════════════════════════════════════╝")
    print()

    lang = _prompt("  Choose language / 选择语言 (en/zh)", default="en").lower()
    if lang.startswith("zh"):
        T = TEXTS["zh"]
    else:
        T = TEXTS["en"]

    existing_env = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    existing_env[k.strip()] = v.strip().strip("\"'")

    print()
    print(_t("intro_1"))
    print(_t("intro_2"))
    print(_t("intro_3"))
    print()

    config = {}

    # ── Step 1: LLM Provider ──
    print("─" * 44)
    print(f"  {_t('step1_title')}")
    print("─" * 44)
    print()
    print(f"  {_t('step1_desc1')}")
    print(f"  {_t('step1_desc2')}")
    print()

    prev_ds = existing_env.get("DEEPSEEK_API_KEY", "")
    if prev_ds:
        print(f"  {_t('existing_key_hint')}")
    deepseek_key = _prompt(f"  {_t('deepseek_key_prompt')}", default=prev_ds)
    if deepseek_key:
        config["DEEPSEEK_API_KEY"] = deepseek_key
        config["DEEPSEEK_BASE_URL"] = _prompt(
            f"  {_t('deepseek_url_prompt')}",
            default=existing_env.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        )
    elif not prev_ds:
        print(f"  {_t('skipped_deepseek')}")

    print()

    # ── Step 2: RAG ──
    print("─" * 44)
    print(f"  {_t('step2_title')}")
    print("─" * 44)
    print()
    print(f"  {_t('step2_desc1')}")
    print(f"  {_t('step2_desc2')}")
    print()

    prev_ds_scope = existing_env.get("DASHSCOPE_API_KEY", "")
    if prev_ds_scope:
        print(f"  {_t('existing_key_hint')}")
    dashscope_key = _prompt(f"  {_t('dashscope_key_prompt')}", default=prev_ds_scope)
    if dashscope_key:
        config["DASHSCOPE_API_KEY"] = dashscope_key
    elif not prev_ds_scope:
        print(f"  {_t('rag_disabled')}")

    print()

    # ── Step 3: MCP Servers ──
    print("─" * 44)
    print(f"  {_t('step3_title')}")
    print("─" * 44)
    print()
    print(f"  {_t('step3_desc1')}")
    print()
    print(f"  {_t('step3_intro')}")
    print()

    mcp_servers = []
    user_indices, has_custom = _multi_select(PRESET_MCP)
    print()

    for i in user_indices:
        if isinstance(i, dict):
            mcp_servers.append(i)
        else:
            preset = PRESET_MCP[i]
            mcp_servers.append({
                "name": preset["name"],
                "command": preset["command"],
                "args": preset["args"],
                "env": preset.get("env", {}),
            })
            print(f"    ✓ {preset['name']}")

    tavily_selected = any(s.get("name") == "tavily" for s in mcp_servers)
    if tavily_selected:
        print()
        prev_tavily = existing_env.get("TAVILY_API_KEY", "")
        if prev_tavily:
            print(f"  {_t('existing_key_hint')}")
        tavily_key = _prompt(f"  {_t('tavily_key_prompt')}", default=prev_tavily)
        if tavily_key:
            config["TAVILY_API_KEY"] = tavily_key
        elif not prev_tavily:
            print(f"  {_t('tavily_key_skipped')}")

    if has_custom and not mcp_servers:
        pass

    print()

    # ── Save ──
    print("─" * 44)
    print(f"  {_t('save_title')}")
    print("─" * 44)
    print()

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if config:
        env_path = ENV_FILE
        existing = {}
        if env_path.exists():
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        existing[k.strip()] = v.strip().strip("\"'")

        existing.update(config)
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("# Lukawi Agent — Environment Configuration\n")
            f.write("# Generated by lukawi-init\n\n")
            for k, v in existing.items():
                if " " in v or v == "":
                    f.write(f'{k}="{v}"\n')
                else:
                    f.write(f"{k}={v}\n")
        print(f"  {_t('wrote_env')} {env_path}")
    else:
        print(f"  {_t('no_keys')}")

    with open(MCP_CONFIG, "w", encoding="utf-8") as f:
        json.dump(mcp_servers, f, indent=2)
        f.write("\n")
    if mcp_servers:
        print(f"  {_t('wrote_mcp')} {MCP_CONFIG} ({len(mcp_servers)} server(s))")
    else:
        print(f"  {_t('wrote_mcp_empty').format(path=MCP_CONFIG)}")

    print()
    print("╔══════════════════════════════════════════╗")
    print(f"║           {_t('done_title'):^29}║")
    print("╚══════════════════════════════════════════╝")
    print()
    print(f"  {_t('next_1')}")
    print("       lukawi webui")
    print()
    print(f"  {_t('next_2')}")
    print("       lukawi")
    print()
    print(f"  {_t('next_3')}")
    print(f"       {_t('next_3_detail')}")
    print()
    print(f"  {_t('config_files')}")
    print(f"    .env              → {ENV_FILE}")
    print(f"    mcp-servers.json  → {MCP_CONFIG}")
    print()
    print(f"  {_t('rerun')}")
    print()


if __name__ == "__main__":
    main()
