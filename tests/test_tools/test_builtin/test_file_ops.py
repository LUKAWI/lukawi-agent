"""Tests for file operation tools."""

import pytest
from pathlib import Path

from lukawi.tools.builtin.file_ops import (
    read_file_handler, write_file_handler, edit_file_handler,
    list_dir_handler, register_file_ops,
    READ_FILE_TOOL, WRITE_FILE_TOOL, EDIT_FILE_TOOL, LIST_DIR_TOOL
)
from lukawi.tools.base import ToolResultStatus
from lukawi.tools.registry import ToolRegistry


class TestToolDefinitions:
    def test_read_file_tool(self):
        assert READ_FILE_TOOL.name == "read_file"
        assert READ_FILE_TOOL.category == "filesystem"

    def test_write_file_tool(self):
        assert WRITE_FILE_TOOL.name == "write_file"

    def test_edit_file_tool(self):
        assert EDIT_FILE_TOOL.name == "edit_file"

    def test_list_dir_tool(self):
        assert LIST_DIR_TOOL.name == "list_dir"


class TestReadFile:
    @pytest.mark.asyncio
    async def test_read_success(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!")

        result = await read_file_handler(str(test_file))

        assert result.status == ToolResultStatus.SUCCESS
        assert result.result == "Hello, world!"

    @pytest.mark.asyncio
    async def test_read_not_found(self):
        result = await read_file_handler("/nonexistent/file.txt")

        assert result.status == ToolResultStatus.ERROR
        assert "not found" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_read_not_a_file(self, tmp_path):
        result = await read_file_handler(str(tmp_path))

        assert result.status == ToolResultStatus.ERROR


class TestWriteFile:
    @pytest.mark.asyncio
    async def test_write_success(self, tmp_path):
        test_file = tmp_path / "output.txt"

        result = await write_file_handler(str(test_file), "content")

        assert result.status == ToolResultStatus.SUCCESS
        assert test_file.read_text() == "content"

    @pytest.mark.asyncio
    async def test_write_creates_dirs(self, tmp_path):
        test_file = tmp_path / "subdir" / "output.txt"

        result = await write_file_handler(str(test_file), "content")

        assert result.status == ToolResultStatus.SUCCESS
        assert test_file.exists()


class TestEditFile:
    @pytest.mark.asyncio
    async def test_edit_success(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!")

        result = await edit_file_handler(str(test_file), "world", "Python")

        assert result.status == ToolResultStatus.SUCCESS
        assert test_file.read_text() == "Hello, Python!"

    @pytest.mark.asyncio
    async def test_edit_not_found_text(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!")

        result = await edit_file_handler(str(test_file), "missing", "new")

        assert result.status == ToolResultStatus.ERROR

    @pytest.mark.asyncio
    async def test_edit_file_not_found(self):
        result = await edit_file_handler("/nonexistent/file.txt", "old", "new")

        assert result.status == ToolResultStatus.ERROR


class TestListDir:
    @pytest.mark.asyncio
    async def test_list_success(self, tmp_path):
        (tmp_path / "file.txt").write_text("content")
        (tmp_path / "subdir").mkdir()

        result = await list_dir_handler(str(tmp_path))

        assert result.status == ToolResultStatus.SUCCESS
        assert len(result.result) == 2

    @pytest.mark.asyncio
    async def test_list_recursive(self, tmp_path):
        (tmp_path / "file.txt").write_text("content")
        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "nested.txt").write_text("nested")

        result = await list_dir_handler(str(tmp_path), recursive=True)

        assert result.status == ToolResultStatus.SUCCESS
        assert len(result.result) == 3

    @pytest.mark.asyncio
    async def test_list_not_found(self):
        result = await list_dir_handler("/nonexistent/dir")

        assert result.status == ToolResultStatus.ERROR

    @pytest.mark.asyncio
    async def test_list_not_a_dir(self, tmp_path):
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")

        result = await list_dir_handler(str(test_file))

        assert result.status == ToolResultStatus.ERROR


class TestRegisterFileOps:
    def test_register_all(self):
        registry = ToolRegistry()
        register_file_ops(registry)

        assert registry.has("read_file")
        assert registry.has("write_file")
        assert registry.has("edit_file")
        assert registry.has("list_dir")
        assert registry.count == 4
