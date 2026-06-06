"""Shell execution tool."""

from __future__ import annotations

import asyncio
import platform
import shlex
from pathlib import Path

from lukawi.tools.base import (
    ToolDefinition, ToolResult, ToolParameter, ToolParameterType,
)


ALLOWED_COMMANDS: set[str] = {
    "dir", "type", "echo", "find", "where",
    "git", "python", "pip",
    "ls", "cat", "pwd", "which", "head", "tail", "wc",
    "date", "time", "whoami", "hostname",
}

CMD_BUILTINS: set[str] = {"dir", "type", "echo", "date", "time"}

SENSITIVE_DIR_PARTS = [
    "\\Windows\\System32",
    "\\Windows",
    "\\Program Files (x86)",
    "\\Program Files",
]

DANGEROUS_PATTERNS = [
    "rm -rf /", "rm -rf ~", "rm -rf .",
    "rmdir /s /q C:\\", "rmdir /s /q D:\\",
    "format ", "fdisk", "diskpart",
    "del /f /s /q", "del /f /s /q C:\\", "del /f /s /q D:\\",
    ":(){:|:&};:", "fork bomb",
    "mkfs", "mke2fs", "mkfs.",
    "dd if=", "dd if=/dev/",
    "shutdown", "reboot", "poweroff", "halt",
    "sudo rm", "sudo dd",
    "wget -O -|", "curl |",
    "chmod 777 /", "chmod -R 777 /",
    "> /dev/sda", "> /dev/", ">> /dev/sd",
    "Set-ExecutionPolicy", "Remove-Item -Recurse -Force C:\\",
]

SHELL_OPERATORS = {";", "&", "|", "`", "$"}

ALLOWED_COMMANDS_STR = ", ".join(sorted(ALLOWED_COMMANDS))

EXEC_COMMAND_TOOL = ToolDefinition(
    name="exec_command",
    description=(
        f"Execute a whitelisted shell command. "
        f"Allowed commands: {ALLOWED_COMMANDS_STR}. "
        "Shell operators (;, &&, ||, |, $(...), backticks, >, <) are not allowed."
    ),
    parameters=[
        ToolParameter(
            name="command",
            type=ToolParameterType.STRING,
            description=(
                f"Command to execute. Must be one of: {ALLOWED_COMMANDS_STR}. "
                "No shell operators allowed."
            )
        ),
        ToolParameter(
            name="cwd",
            type=ToolParameterType.STRING,
            description="Working directory. Cannot be a system directory.",
            required=False,
            default=None
        ),
        ToolParameter(
            name="timeout",
            type=ToolParameterType.NUMBER,
            description="Timeout in seconds",
            required=False,
            default=30
        )
    ],
    category="system",
    tags=["shell", "command", "execute"]
)


def _is_dangerous_command(command: str) -> bool:
    command_lower = command.lower().strip()

    for pattern in DANGEROUS_PATTERNS:
        if pattern.lower() in command_lower:
            return True

    return False


def _has_shell_operators(command: str) -> bool:
    for ch in SHELL_OPERATORS:
        if ch in command:
            return True
    if ">" in command:
        return True
    if "<" in command:
        return True
    return False


def _is_sensitive_path(path: str | Path) -> bool:
    resolved = Path(path).resolve()
    path_str = str(resolved)
    for part in SENSITIVE_DIR_PARTS:
        if part.lower() in path_str.lower():
            return True
    return False


def _strip_outer_quotes(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] and token[0] in ('"', "'"):
        return token[1:-1]
    return token


def _tokenize_command(command: str) -> list[str]:
    try:
        if platform.system() == "Windows":
            tokens = shlex.split(command, posix=False)
        else:
            tokens = shlex.split(command)
        return [_strip_outer_quotes(t) for t in tokens]
    except ValueError:
        return []


async def exec_command_handler(
    command: str,
    cwd: str | None = None,
    timeout: float = 30
) -> ToolResult:
    if _is_dangerous_command(command):
        return ToolResult.denied(
            "Command blocked: matches dangerous pattern"
        )

    tokens = _tokenize_command(command)
    if not tokens:
        return ToolResult.error("Empty command")

    cmd_name = tokens[0].lower()

    if cmd_name not in ALLOWED_COMMANDS:
        return ToolResult.denied(
            f"Command '{cmd_name}' is not in the allowed commands whitelist"
        )

    using_cmd_exe = platform.system() == "Windows" and cmd_name in CMD_BUILTINS

    if using_cmd_exe and _has_shell_operators(command):
        return ToolResult.denied(
            "Command blocked: shell operators are not allowed"
        )

    if cwd:
        resolved_cwd = Path(cwd).resolve()
        if not resolved_cwd.exists():
            return ToolResult.error(f"Working directory does not exist: {resolved_cwd}")
        if _is_sensitive_path(resolved_cwd):
            return ToolResult.denied(
                f"Cannot execute in sensitive directory: {resolved_cwd}"
            )
        working_dir = str(resolved_cwd)
    else:
        working_dir = None

    try:
        args = tokens[1:]
        create_kwargs = {
            "stdout": asyncio.subprocess.PIPE,
            "stderr": asyncio.subprocess.PIPE,
            "cwd": working_dir,
        }

        if using_cmd_exe:
            cmd_for_exec = command
            if cmd_name in ("date", "time") and "/t" not in command.lower():
                cmd_for_exec = f"{command} /t"
            proc = await asyncio.create_subprocess_exec(
                "cmd.exe", "/c", cmd_for_exec,
                **create_kwargs
            )
        else:
            proc = await asyncio.create_subprocess_exec(
                cmd_name, *args,
                **create_kwargs
            )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return ToolResult.timeout(
                f"Command timed out after {timeout}s"
            )

        stdout_str = stdout.decode("utf-8", errors="replace")
        stderr_str = stderr.decode("utf-8", errors="replace")

        if proc.returncode == 0:
            return ToolResult.success(
                result=stdout_str,
                metadata={
                    "exit_code": proc.returncode,
                    "stderr": stderr_str if stderr_str else None
                }
            )
        else:
            return ToolResult.error(
                f"Command failed with exit code {proc.returncode}: {stderr_str}"
            )

    except FileNotFoundError:
        return ToolResult.error(f"Command '{cmd_name}' not found")
    except Exception as e:
        return ToolResult.error(f"Failed to execute command: {str(e)}")


def register_shell(registry) -> None:
    registry.register(EXEC_COMMAND_TOOL, exec_command_handler)
