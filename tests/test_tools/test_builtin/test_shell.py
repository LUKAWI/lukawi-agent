"""Tests for shell execution tool."""

import pytest
import platform
from pathlib import Path

from lukawi.tools.builtin.shell import (
    exec_command_handler, EXEC_COMMAND_TOOL, register_shell,
    _is_dangerous_command, _has_shell_operators,
    _is_sensitive_path, _tokenize_command, ALLOWED_COMMANDS,
)
from lukawi.tools.base import ToolResultStatus
from lukawi.tools.registry import ToolRegistry


class TestToolDefinition:
    def test_tool_definition(self):
        assert EXEC_COMMAND_TOOL.name == "exec_command"
        assert EXEC_COMMAND_TOOL.category == "system"

    def test_description_includes_allowed_commands(self):
        for cmd in ALLOWED_COMMANDS:
            assert cmd in EXEC_COMMAND_TOOL.description


class TestDangerousCommands:
    def test_dangerous_patterns(self):
        assert _is_dangerous_command("rm -rf /")
        assert _is_dangerous_command("rm -rf /home")
        assert _is_dangerous_command(":(){:|:&};:")
        assert _is_dangerous_command("mkfs.ext4 /dev/sda")

    def test_safe_commands(self):
        assert not _is_dangerous_command("ls -la")
        assert not _is_dangerous_command("echo hello")
        assert not _is_dangerous_command("cat file.txt")


class TestShellOperators:
    def test_detects_shell_operators(self):
        assert _has_shell_operators("dir; rm -rf /")
        assert _has_shell_operators("echo hello && world")
        assert _has_shell_operators("ls | grep foo")
        assert _has_shell_operators("cat file > output")
        assert _has_shell_operators("echo $(whoami)")
        assert _has_shell_operators("echo `whoami`")

    def test_allows_safe_commands(self):
        assert not _has_shell_operators("dir C:\\Users")
        assert not _has_shell_operators("echo hello world")
        assert not _has_shell_operators("git status")
        assert not _has_shell_operators("where python")


class TestSensitivePath:
    def test_detects_sensitive_paths(self):
        assert _is_sensitive_path("C:\\Windows")
        assert _is_sensitive_path("C:\\Windows\\System32")
        assert _is_sensitive_path("C:\\Program Files")
        assert _is_sensitive_path("D:\\Program Files (x86)\\SomeApp")

    def test_allows_safe_paths(self, tmp_path):
        assert not _is_sensitive_path(str(tmp_path))
        assert not _is_sensitive_path("C:\\Users\\test\\Documents")
        assert not _is_sensitive_path("D:\\projects")
        assert not _is_sensitive_path("C:\\Users\\test\\AppData\\Local\\Temp")


class TestTokenizeCommand:
    def test_simple_command(self):
        tokens = _tokenize_command("echo hello world")
        assert tokens == ["echo", "hello", "world"]

    def test_command_with_quotes(self):
        tokens = _tokenize_command('git commit -m "initial commit"')
        assert tokens == ["git", "commit", "-m", "initial commit"]

    def test_windows_path(self):
        tokens = _tokenize_command("dir C:\\Users")
        assert tokens == ["dir", "C:\\Users"]

    def test_empty_command(self):
        assert _tokenize_command("") == []
        assert _tokenize_command("   ") == []

    def test_unmatched_quotes(self):
        assert _tokenize_command('echo "hello') == []


class TestWhitelist:
    @pytest.mark.asyncio
    async def test_allowed_command_succeeds(self):
        result = await exec_command_handler("echo hello")
        assert result.status == ToolResultStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_disallowed_command_denied(self):
        result = await exec_command_handler("sudo rm -rf /")
        assert result.status == ToolResultStatus.DENIED

    @pytest.mark.asyncio
    async def test_nonexistent_command_denied(self):
        result = await exec_command_handler("nonexistent_command_12345")
        assert result.status == ToolResultStatus.DENIED


class TestExecCommand:
    @pytest.mark.asyncio
    async def test_success(self):
        result = await exec_command_handler("echo hello")
        assert result.status == ToolResultStatus.SUCCESS
        assert "hello" in result.result.lower()

    @pytest.mark.asyncio
    async def test_with_cwd(self, tmp_path):
        result = await exec_command_handler("echo hello", cwd=str(tmp_path))
        assert result.status == ToolResultStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_sensitive_cwd_denied(self):
        result = await exec_command_handler(
            "echo hello", cwd="C:\\Windows\\System32"
        )
        assert result.status == ToolResultStatus.DENIED

    @pytest.mark.asyncio
    async def test_nonexistent_cwd_error(self, tmp_path):
        bad_path = str(tmp_path / "does_not_exist")
        result = await exec_command_handler("echo hello", cwd=bad_path)
        assert result.status == ToolResultStatus.ERROR

    @pytest.mark.asyncio
    async def test_timeout(self):
        result = await exec_command_handler(
            "python -c \"import time; time.sleep(10)\"",
            timeout=0.1
        )
        assert result.status == ToolResultStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_dangerous_command_denied(self):
        result = await exec_command_handler("rm -rf /")
        assert result.status == ToolResultStatus.DENIED

    @pytest.mark.asyncio
    async def test_shell_operators_via_cmd_builtin_denied(self):
        if platform.system() == "Windows":
            result = await exec_command_handler("dir; echo hello")
            assert result.status == ToolResultStatus.DENIED

    @pytest.mark.asyncio
    async def test_shell_operators_in_args_allowed(self):
        result = await exec_command_handler(
            "python -c \"print('hello | world'); print('done')\""
        )
        assert result.status == ToolResultStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_failed_command(self):
        result = await exec_command_handler(
            "python -c \"raise RuntimeError('fail')\""
        )
        assert result.status == ToolResultStatus.ERROR


class TestRegisterShell:
    def test_register(self):
        registry = ToolRegistry()
        register_shell(registry)
        assert registry.has("exec_command")
