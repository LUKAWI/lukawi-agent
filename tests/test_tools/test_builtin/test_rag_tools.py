"""Tests for RAG tools registration and handlers."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

from lukawi.tools.base import ToolParameterType, ToolResultStatus
from lukawi.tools.builtin.rag_search import (
    RAG_SEARCH_TOOL,
    RAG_UPLOAD_TOOL,
    RAG_LIST_TOOL,
    register_rag_tools,
)
from lukawi.tools.registry import ToolRegistry


class FakeRAGManager:
    def __init__(self):
        self._search_results = []
        self._upload_result = {"filename": "test.md", "chunks": 3, "replaced": False}
        self._docs = []

    async def search(self, query, sources=None, limit=5, source_path=None):
        return self._search_results

    async def upload_document(self, file_path):
        return dict(self._upload_result)

    async def list_documents(self):
        return list(self._docs)


class TestRAGToolDefinitions:
    def test_rag_search_tool_name(self):
        assert RAG_SEARCH_TOOL.name == "rag_search"

    def test_rag_search_tool_has_query_param(self):
        params = {p.name: p for p in RAG_SEARCH_TOOL.parameters}
        assert "query" in params
        assert params["query"].type == ToolParameterType.STRING

    def test_rag_search_tool_has_source_param(self):
        params = {p.name: p for p in RAG_SEARCH_TOOL.parameters}
        assert "source" in params
        assert params["source"].required is False
        assert params["source"].default == "all"

    def test_rag_search_tool_has_file_param(self):
        params = {p.name: p for p in RAG_SEARCH_TOOL.parameters}
        assert "file" in params
        assert params["file"].required is False
        assert params["file"].default == ""

    def test_rag_search_tool_has_limit_param(self):
        params = {p.name: p for p in RAG_SEARCH_TOOL.parameters}
        assert "limit" in params
        assert params["limit"].type == ToolParameterType.INTEGER
        assert params["limit"].default == 5

    def test_rag_upload_tool_name(self):
        assert RAG_UPLOAD_TOOL.name == "rag_upload"

    def test_rag_upload_tool_has_path_param(self):
        params = {p.name: p for p in RAG_UPLOAD_TOOL.parameters}
        assert "path" in params
        assert params["path"].type == ToolParameterType.STRING

    def test_rag_list_tool_name(self):
        assert RAG_LIST_TOOL.name == "rag_list"

    def test_rag_list_tool_no_params(self):
        assert len(RAG_LIST_TOOL.parameters) == 0

    def test_rag_search_category(self):
        assert RAG_SEARCH_TOOL.category == "rag"

    def test_rag_upload_category(self):
        assert RAG_UPLOAD_TOOL.category == "rag"

    def test_rag_list_category(self):
        assert RAG_LIST_TOOL.category == "rag"


class TestRAGToolsRegistration:
    def test_register_with_rag_manager(self):
        registry = ToolRegistry()
        register_rag_tools(registry, rag_manager=FakeRAGManager())
        assert registry.has("rag_search")
        assert registry.has("rag_upload")
        assert registry.has("rag_list")

    def test_register_without_rag_manager(self):
        registry = ToolRegistry()
        register_rag_tools(registry, rag_manager=None)
        assert registry.has("rag_search")
        assert registry.has("rag_upload")
        assert registry.has("rag_list")

    def test_registered_handlers_are_callable(self):
        registry = ToolRegistry()
        register_rag_tools(registry, rag_manager=None)
        for name in ("rag_search", "rag_upload", "rag_list"):
            _, handler = registry.get(name)
            assert callable(handler)


@pytest.mark.asyncio
async def test_search_without_manager_returns_error():
    registry = ToolRegistry()
    register_rag_tools(registry, rag_manager=None)
    _, handler = registry.get("rag_search")
    result = await handler(query="test")
    assert result.status == ToolResultStatus.ERROR


@pytest.mark.asyncio
async def test_upload_without_manager_returns_error():
    registry = ToolRegistry()
    register_rag_tools(registry, rag_manager=None)
    _, handler = registry.get("rag_upload")
    result = await handler(path="/tmp/test.md")
    assert result.status == ToolResultStatus.ERROR


@pytest.mark.asyncio
async def test_list_without_manager_returns_error():
    registry = ToolRegistry()
    register_rag_tools(registry, rag_manager=None)
    _, handler = registry.get("rag_list")
    result = await handler()
    assert result.status == ToolResultStatus.ERROR


@pytest.mark.asyncio
async def test_search_returns_results():
    mgr = FakeRAGManager()
    mgr._search_results = [
        MagicMock(
            content="Lukawi Agent 框架支持 RAG",
            score=0.95,
            metadata={"source_path": "guide.md", "type": "document"},
        ),
        MagicMock(
            content="ReAct 循环与工具调用",
            score=0.85,
            metadata={"source_path": "architecture.md", "type": "document"},
        ),
    ]

    registry = ToolRegistry()
    register_rag_tools(registry, rag_manager=mgr)
    _, handler = registry.get("rag_search")

    result = await handler(query="RAG")
    assert result.status == ToolResultStatus.SUCCESS
    assert result.metadata["count"] == 2
    assert result.result[0]["content"] == "Lukawi Agent 框架支持 RAG"
    assert result.result[0]["score"] == 0.95


@pytest.mark.asyncio
async def test_search_empty_results():
    mgr = FakeRAGManager()

    registry = ToolRegistry()
    register_rag_tools(registry, rag_manager=mgr)
    _, handler = registry.get("rag_search")

    result = await handler(query="nothing")
    assert result.status == ToolResultStatus.SUCCESS
    assert result.metadata["count"] == 0
    assert "未找到" in str(result.result)


@pytest.mark.asyncio
async def test_search_invalid_source():
    registry = ToolRegistry()
    register_rag_tools(registry, rag_manager=FakeRAGManager())
    _, handler = registry.get("rag_search")

    result = await handler(query="test", source="invalid")
    assert result.status == ToolResultStatus.ERROR


@pytest.mark.asyncio
async def test_upload_success(tmp_path):
    mgr = FakeRAGManager()
    mgr._upload_result = {"filename": "test.md", "chunks": 5, "replaced": False}

    registry = ToolRegistry()
    register_rag_tools(registry, rag_manager=mgr)
    _, handler = registry.get("rag_upload")

    result = await handler(path="/tmp/test.md")
    assert result.status == ToolResultStatus.SUCCESS
    assert "上传成功" in str(result.result)
    assert "5 个文本块" in str(result.result)


@pytest.mark.asyncio
async def test_upload_replaced():
    mgr = FakeRAGManager()
    mgr._upload_result = {"filename": "test.md", "chunks": 3, "replaced": True}

    registry = ToolRegistry()
    register_rag_tools(registry, rag_manager=mgr)
    _, handler = registry.get("rag_upload")

    result = await handler(path="/tmp/test.md")
    assert result.status == ToolResultStatus.SUCCESS
    assert "已覆盖旧版本" in str(result.result)


@pytest.mark.asyncio
async def test_list_empty():
    registry = ToolRegistry()
    register_rag_tools(registry, rag_manager=FakeRAGManager())
    _, handler = registry.get("rag_list")

    result = await handler()
    assert result.status == ToolResultStatus.SUCCESS
    assert "知识库为空" in str(result.result)


@pytest.mark.asyncio
async def test_list_with_docs():
    mgr = FakeRAGManager()
    mgr._docs = [
        {"filename": "guide.md", "chunks": 5},
        {"filename": "notes.txt", "chunks": 3},
    ]

    registry = ToolRegistry()
    register_rag_tools(registry, rag_manager=mgr)
    _, handler = registry.get("rag_list")

    result = await handler()
    assert result.status == ToolResultStatus.SUCCESS
    assert len(result.result) == 2
    assert result.metadata["total"] == 2
