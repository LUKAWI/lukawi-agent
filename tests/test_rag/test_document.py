"""Tests for DocumentLoader."""

from __future__ import annotations

from pathlib import Path

import pytest

from lukawi.rag.document import DocumentChunk, DocumentLoader
from lukawi.rag.exceptions import DocumentLoadError


# ── helpers ──────────────────────────────────────────────────────────────────

def _write(path: Path, content: str, encoding: str = "utf-8") -> None:
    path.write_text(content, encoding=encoding)


def _write_bytes(path: Path, data: bytes) -> None:
    path.write_bytes(data)


# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_text_file(tmp_path: Path) -> Path:
    p = tmp_path / "sample.txt"
    _write(p, "Lukawi Agent 是一个轻量级 AI 框架。\n\n它使用 ReAct 循环进行推理。\n支持多种工具调用。")
    return p


@pytest.fixture
def sample_markdown_file(tmp_path: Path) -> Path:
    p = tmp_path / "sample.md"
    _write(p, "# Lukawi Agent\n\nThis is a **markdown** file.\n\nIt has multiple paragraphs.")
    return p


@pytest.fixture
def gbk_encoded_file(tmp_path: Path) -> Path:
    p = tmp_path / "gbk.txt"
    _write(p, "中文技术文档内容测试", encoding="gbk")
    return p


@pytest.fixture
def utf8_bom_file(tmp_path: Path) -> Path:
    p = tmp_path / "bom.txt"
    _write_bytes(p, b"\xef\xbb\xbfhello world\n")
    return p


@pytest.fixture
def small_text_file(tmp_path: Path) -> Path:
    p = tmp_path / "small.txt"
    _write(p, "短文本。")
    return p


@pytest.fixture
def medium_text_file(tmp_path: Path) -> Path:
    p = tmp_path / "medium.txt"
    sentences = "。".join(f"这是第{i}句话" for i in range(1, 20)) + "。"
    _write(p, sentences)
    return p


# ── TestDocumentLoaderInit ───────────────────────────────────────────────────

class TestDocumentLoaderInit:
    """Tests for DocumentLoader.__init__."""

    def test_default_chunk_size(self) -> None:
        loader = DocumentLoader()
        assert loader.chunk_size == 500
        assert loader.chunk_overlap == 50

    def test_custom_chunk_size(self) -> None:
        loader = DocumentLoader(chunk_size=300, chunk_overlap=30)
        assert loader.chunk_size == 300
        assert loader.chunk_overlap == 30


# ── TestLoadFile ─────────────────────────────────────────────────────────────

class TestLoadFile:
    """Tests for DocumentLoader.load_file."""

    def test_load_txt_returns_chunks(self, sample_text_file: Path) -> None:
        loader = DocumentLoader()
        chunks = loader.load_file(sample_text_file)
        assert len(chunks) >= 1
        assert all(isinstance(c, DocumentChunk) for c in chunks)

    def test_txt_chunk_contains_content(self, sample_text_file: Path) -> None:
        loader = DocumentLoader()
        chunks = loader.load_file(sample_text_file)
        combined = "".join(c.content for c in chunks)
        assert "Lukawi Agent" in combined

    def test_txt_chunk_has_metadata(self, sample_text_file: Path) -> None:
        loader = DocumentLoader()
        chunks = loader.load_file(sample_text_file)
        assert len(chunks) > 0
        first = chunks[0]
        assert first.source_path == str(sample_text_file)
        assert first.chunk_index == 0

    def test_load_md_returns_chunks(self, sample_markdown_file: Path) -> None:
        loader = DocumentLoader()
        chunks = loader.load_file(sample_markdown_file)
        assert len(chunks) >= 1

    def test_load_nonexistent_file_raises(self) -> None:
        loader = DocumentLoader()
        with pytest.raises(DocumentLoadError, match="不存在"):
            loader.load_file(Path("/nonexistent/path/file.txt"))

    def test_load_directory_returns_nonexistent(self) -> None:
        loader = DocumentLoader()
        with pytest.raises(DocumentLoadError):
            loader.load_directory(Path("/nonexistent/directory"))


# ── TestEncodingFallback ─────────────────────────────────────────────────────

class TestEncodingFallback:
    """Tests for DocumentLoader encoding fallback."""

    def test_read_gbk_encoded_file(self, gbk_encoded_file: Path) -> None:
        loader = DocumentLoader()
        chunks = loader.load_file(gbk_encoded_file)
        assert len(chunks) >= 1
        assert "中文技术文档" in chunks[0].content

    def test_read_utf8_with_bom(self, utf8_bom_file: Path) -> None:
        loader = DocumentLoader()
        chunks = loader.load_file(utf8_bom_file)
        assert len(chunks) >= 1
        assert "hello world" in chunks[0].content


# ── TestChunkBoundaries ──────────────────────────────────────────────────────

class TestChunkBoundaries:
    """Tests for chunk splitting boundaries and uniqueness."""

    def test_small_file_single_chunk(self, small_text_file: Path) -> None:
        loader = DocumentLoader()
        chunks = loader.load_file(small_text_file)
        assert len(chunks) == 1

    def test_chunks_have_unique_ids(self, medium_text_file: Path) -> None:
        loader = DocumentLoader(chunk_size=50, chunk_overlap=10)
        chunks = loader.load_file(medium_text_file)
        ids = [c.id for c in chunks]
        assert len(ids) == len(set(ids))

    def test_chunks_indexed_sequentially(self, medium_text_file: Path) -> None:
        loader = DocumentLoader(chunk_size=50, chunk_overlap=10)
        chunks = loader.load_file(medium_text_file)
        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))
