import json
from pathlib import Path

from lukawi.config.user_config import load_mcp_servers, save_mcp_servers
from lukawi.mcp.client import MCPServerConfig
from lukawi.commands.handler import CommandContext, CommandHandler


class McpCommand(CommandHandler):
    name = "/mcp"
    description = "Manage MCP servers"
    usage = "/mcp <list|add|remove|connect|disconnect|import>"
    category = "mcp"

    async def execute(self, args: list[str], ctx: CommandContext) -> str:
        if not args:
            return (
                "Usage: `/mcp list`, `/mcp add <name> <command> [args...]`, "
                "`/mcp remove <name>`, `/mcp connect`, `/mcp disconnect`, "
                "`/mcp import <file.json>`"
            )

        sub = args[0]

        if sub == "list":
            return self._list(ctx)
        elif sub == "add" and len(args) >= 3:
            return await self._add(args[1:], ctx)
        elif sub == "remove" and len(args) >= 2:
            return await self._remove(args[1], ctx)
        elif sub == "connect":
            return await self._connect(ctx)
        elif sub == "disconnect":
            return await self._disconnect(ctx)
        elif sub == "import" and len(args) >= 2:
            return self._import_servers(args[1], ctx)
        else:
            return (
                "Usage: `/mcp list`, `/mcp add <name> <command> [args...]`, "
                "`/mcp remove <name>`, `/mcp connect`, `/mcp disconnect`, "
                "`/mcp import <file.json>`"
            )

    def _list(self, ctx: CommandContext) -> str:
        user_servers = load_mcp_servers()
        mcp = ctx.mcp_manager
        if not user_servers and not (mcp and mcp.connected_count > 0):
            return "No MCP servers configured."
        connected = mcp.connected_servers if mcp else []
        lines = ["**MCP Servers:**"]
        for s in user_servers:
            status = "connected" if s.name in connected else "disconnected"
            marker = "+" if s.name in connected else " "
            lines.append(f"- [{marker}] {s.name}: {s.command} ({status})")
        return "\n".join(lines)

    async def _add(self, args: list[str], ctx: CommandContext) -> str:
        name = args[0]
        cmd = args[1]
        cmd_args = args[2:] if len(args) > 2 else []
        new_server = MCPServerConfig(name=name, command=[cmd], args=cmd_args)

        user_servers = load_mcp_servers()
        user_servers = [s for s in user_servers if s.name != name]
        user_servers.append(new_server)
        save_mcp_servers(user_servers)

        lines = [f"MCP server '{name}' saved to ~/.lukawi/mcp-servers.json"]

        if ctx.mcp_manager:
            tool_registry = getattr(ctx.app, "tool_registry", None)
            ok = await ctx.mcp_manager.connect_server(new_server, tool_registry)
            if ok:
                lines.append(
                    f"MCP server '{name}' connected and tools registered."
                )
            else:
                lines.append(f"Failed to connect '{name}'. Check the command.")

        return "\n".join(lines)

    async def _remove(self, name: str, ctx: CommandContext) -> str:
        if ctx.mcp_manager and name in ctx.mcp_manager.connected_servers:
            await ctx.mcp_manager.disconnect_server(name)
        user_servers = load_mcp_servers()
        user_servers = [s for s in user_servers if s.name != name]
        save_mcp_servers(user_servers)
        return f"MCP server '{name}' removed and disconnected."

    async def _connect(self, ctx: CommandContext) -> str:
        if not ctx.mcp_manager:
            return "No MCP manager available."
        user_servers = load_mcp_servers()
        if not user_servers:
            return "No MCP servers configured. Use `/mcp add` first."
        await ctx.mcp_manager.connect_all(user_servers)
        tool_registry = getattr(ctx.app, "tool_registry", None)
        await ctx.mcp_manager.register_tools(tool_registry)
        setattr(ctx.app, "_mcp_connected", True)
        return f"Connected {len(user_servers)} MCP server(s)."

    async def _disconnect(self, ctx: CommandContext) -> str:
        if not ctx.mcp_manager:
            return "No MCP manager available."
        await ctx.mcp_manager.disconnect_all()
        return "All MCP servers disconnected."

    def _import_servers(self, filepath: str, ctx: CommandContext) -> str:
        try:
            data = json.loads(Path(filepath).read_text(encoding="utf-8"))
            imported = [
                MCPServerConfig(
                    name=item["name"],
                    command=item.get("command", []),
                    args=item.get("args", []),
                )
                for item in data
                if "name" in item
            ]
            user = load_mcp_servers()
            by_name = {s.name: s for s in user}
            for s in imported:
                by_name[s.name] = s
            merged = list(by_name.values())
            save_mcp_servers(merged)
            return f"Imported {len(imported)} MCP server(s) from {filepath}."
        except FileNotFoundError:
            return f"File not found: {filepath}"
        except Exception as e:
            return f"Import failed: {e}"
