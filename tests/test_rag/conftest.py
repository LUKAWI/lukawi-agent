"""Shared fixtures for RAG tests."""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def sample_text_file(temp_dir):
    path = temp_dir / "sample.txt"
    path.write_text(
        (
            "Lukawi Agent 是一个轻量级 AI Agent 框架。\n"
            "它支持 ReAct 循环、工具调用和记忆系统。\n"
            "技术栈包括 Python、DeepSeek API 和 Textual TUI。\n"
        ),
        encoding="utf-8",
    )
    return path


@pytest.fixture
def sample_markdown_file(temp_dir):
    path = temp_dir / "sample.md"
    path.write_text(
        (
            "# 系统架构\n\n"
            "## 核心模块\n\n"
            "- Agent 核心引擎\n"
            "- LLM 抽象层\n"
            "- 工具管理系统\n"
            "- 记忆系统\n\n"
            "## 数据流\n\n"
            "用户输入 → Agent.think() → Agent.act() → Agent.observe()\n"
        ),
        encoding="utf-8",
    )
    return path


@pytest.fixture
def gbk_encoded_file(temp_dir):
    path = temp_dir / "chinese_gbk.txt"
    path.write_bytes("这是一份中文技术文档\n包含系统架构说明\n".encode("gbk"))
    return path


@pytest.fixture
def mock_embedder():
    return MagicMock()


@pytest.fixture
def mock_store():
    store = MagicMock()
    store.initialize = AsyncMock()
    store.close = MagicMock()
    store.delete_document = AsyncMock(return_value=0)
    store.add_documents = AsyncMock(return_value=[])
    store.add_conversation = AsyncMock(return_value="conv_001")
    return store
