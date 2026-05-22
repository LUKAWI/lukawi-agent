# RAG + 向量检索 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 Lukawi Agent 添加基于 DashScope text-embedding-v3 + ChromaDB 的 RAG 能力，支持本地上传文件检索和对话记录语义搜索，替代现有 SQLite longterm 记忆。

**Architecture:** 新增 `src/lukawi/rag/` 模块（embedder/document/store/retriever/manager），通过注入 RAGManager 替代 MemoryManager 中的 LongTermMemory。注册 3 个新工具（rag_search/rag_upload/rag_list），Agent 自主调用。

**Tech Stack:** DashScope text-embedding-v3 (1024d), ChromaDB ≥0.5.0, 自研 DocumentLoader（句子边界分块，500 token/50 overlap，编码回退 UTF-8→GBK→GB2312）

**Spec:** `docs/superpowers/specs/2026-05-22-rag-vector-search-design.md`

---

## 文件结构总览

```
🆕 src/lukawi/rag/
├── __init__.py               # Task 1
├── exceptions.py             # Task 2
├── embedder.py               # Task 3
├── document.py               # Task 4
├── store.py                  # Task 5
├── retriever.py              # Task 6
└── manager.py                # Task 7

🆕 tests/test_rag/
├── __init__.py
├── conftest.py               # Task 3
├── test_embedder.py          # Task 3
├── test_document.py          # Task 4
├── test_store.py             # Task 5
├── test_retriever.py         # Task 6
└── test_manager.py           # Task 7

🆕 src/lukawi/tools/builtin/rag_search.py   # Task 8

🔧 src/lukawi/config/models.py              # Task 9
🔧 src/lukawi/memory/manager.py             # Task 10
🔧 src/lukawi/memory/longterm.py            # Task 10
🔧 src/lukawi/cli/__init__.py               # Task 11
🔧 src/lukawi/tools/builtin/__init__.py     # Task 8
🔧 src/lukawi/data/default.yaml             # Task 12
🔧 pyproject.toml                           # Task 1
🔧 src/lukawi/agent/core.py                 # Task 13
```

---

### Task 1: 项目依赖与模块骨架

**Files:**
- Create: `src/lukawi/rag/__init__.py`
- Create: `tests/test_rag/__init__.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: 添加依赖到 pyproject.toml**

在 `pyproject.toml` 的 `[project]` → `dependencies` 列表末尾添加 chromadb 和 dashscope：

```toml
dependencies = [
    ...
    "chromadb>=0.5.0",
    "dashscope>=1.20.0",
]
```

在 `[project.optional-dependencies]` → `dev` 添加测试依赖：

```toml
[project.optional-dependencies]
dev = [
    ...
    "pytest-asyncio>=0.24.0",
]
```

- [ ] **Step 2: 安装新依赖**

Run: `pip install -e ".[dev]"`

- [ ] **Step 3: 创建模块骨架**

`src/lukawi/rag/__init__.py`:

```python
"""RAG module — Retrieval-Augmented Generation with DashScope embeddings and ChromaDB."""

from __future__ import annotations

__all__ = [
    "RAGManager",
    "VectorStore",
    "DocumentLoader",
    "DashScopeEmbedder",
    "Retriever",
    "DocumentChunk",
    "SearchResult",
    "EmbeddingResult",
    "RAGError",
    "EmbeddingError",
    "StorageError",
    "DocumentLoadError",
]
```

`tests/test_rag/__init__.py`:

```python
"""Tests for RAG module."""
```

- [ ] **Step 4: 验证安装了 chromadb 和 dashscope**

Run: `python -c "import chromadb; print(chromadb.__version__)"`
Expected: `0.5.x` 或更高

Run: `python -c "import dashscope; print(dashscope.__version__)"`
Expected: `1.20.x` 或更高

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/lukawi/rag/__init__.py tests/test_rag/__init__.py
git commit -m "feat(rag): add chromadb and dashscope dependencies, create rag module skeleton"
```

---

### Task 2: 异常层次

**Files:**
- Create: `src/lukawi/rag/exceptions.py`

- [ ] **Step 1: 创建异常类**

`src/lukawi/rag/exceptions.py`:

```python
"""RAG module exception hierarchy."""

from __future__ import annotations


class RAGError(Exception):
    """Base exception for all RAG module errors."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        full = f"{message}" + (f" (caused by: {cause})" if cause else "")
        super().__init__(full)
        self.cause = cause


class EmbeddingError(RAGError):
    """Embedding API call failed (auth, rate limit, timeout, network)."""
    pass


class StorageError(RAGError):
    """ChromaDB operation failed."""
    pass


class DocumentLoadError(RAGError):
    """File not found, unreadable, or unsupported format."""
    pass
```

- [ ] **Step 2: 验证导入**

Run: `python -c "from lukawi.rag.exceptions import RAGError, EmbeddingError, StorageError, DocumentLoadError; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add src/lukawi/rag/exceptions.py
git commit -m "feat(rag): add exception hierarchy (RAGError, EmbeddingError, StorageError, DocumentLoadError)"
```

---

### Task 3: DashScope Embedding 客户端

**Files:**
- Create: `src/lukawi/rag/embedder.py`
- Create: `tests/test_rag/test_embedder.py`
- Create: `tests/test_rag/conftest.py`

- [ ] **Step 1: 创建 conftest.py**

`tests/test_rag/conftest.py`:

```python
"""Shared fixtures for RAG tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Temporary directory for ChromaDB persistence tests."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def sample_text_file(temp_dir):
    """Create a sample .txt file for document loading tests."""
    path = temp_dir / "sample.txt"
    path.write_text(
        "Lukawi Agent 是一个轻量级 AI Agent 框架。\n"
        "它支持 ReAct 循环、工具调用和记忆系统。\n"
        "技术栈包括 Python、DeepSeek API 和 Textual TUI。\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def sample_markdown_file(temp_dir):
    """Create a sample .md file for document loading tests."""
    path = temp_dir / "sample.md"
    path.write_text(
        "# 系统架构\n\n"
        "## 核心模块\n\n"
        "- Agent 核心引擎\n"
        "- LLM 抽象层\n"
        "- 工具管理系统\n"
        "- 记忆系统\n\n"
        "## 数据流\n\n"
        "用户输入 → Agent.think() → Agent.act() → Agent.observe()\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def gbk_encoded_file(temp_dir):
    """Create a GBK-encoded Chinese file."""
    path = temp_dir / "chinese_gbk.txt"
    path.write_bytes("这是一份中文技术文档\n包含系统架构说明\n".encode("gbk"))
    return path
```

- [ ] **Step 2: 写 failing test — embedder 初始化和单条 embedding**

`tests/test_rag/test_embedder.py`:

```python
"""Tests for DashScopeEmbedder."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from lukawi.rag.embedder import DashScopeEmbedder, EmbeddingResult
from lukawi.rag.exceptions import EmbeddingError


class TestDashScopeEmbedderInit:
    """Test embedder initialization."""

    def test_init_with_defaults(self):
        """Should initialize with default model and dimensions."""
        embedder = DashScopeEmbedder(api_key="sk-test")
        assert embedder.model == "text-embedding-v3"
        assert embedder.dimensions == 1024

    def test_init_with_custom_model(self):
        """Should accept custom model name."""
        embedder = DashScopeEmbedder(api_key="sk-test", model="text-embedding-v2")
        assert embedder.model == "text-embedding-v2"

    def test_init_with_custom_dimensions(self):
        """Should accept custom dimensions."""
        embedder = DashScopeEmbedder(api_key="sk-test", dimensions=768)
        assert embedder.dimensions == 768
```

- [ ] **Step 3: 运行测试验证失败**

Run: `pytest tests/test_rag/test_embedder.py::TestDashScopeEmbedderInit -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'lukawi.rag.embedder'`

- [ ] **Step 4: 实现最小 embedder**

`src/lukawi/rag/embedder.py`:

```python
"""DashScope text-embedding-v3 client."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from lukawi.rag.exceptions import EmbeddingError

logger = logging.getLogger("lukawi.rag.embedder")


@dataclass
class EmbeddingResult:
    """Single embedding API result."""
    embedding: list[float]
    model: str
    tokens_used: int = 0
    metadata: dict = field(default_factory=dict)


class DashScopeEmbedder:
    """Client for DashScope text-embedding-v3 API.

    Uses dashscope.TextEmbedding with exponential backoff retry.
    """

    MAX_BATCH_SIZE = 25

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-v3",
        dimensions: int = 1024,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.dimensions = dimensions

    async def embed(self, texts: str | list[str]) -> list[EmbeddingResult]:
        """Embed one or more texts. Auto-batches if >25 texts."""
        if isinstance(texts, str):
            return [await self.embed_single(texts)]
        results: list[EmbeddingResult] = []
        for i in range(0, len(texts), self.MAX_BATCH_SIZE):
            batch = texts[i : i + self.MAX_BATCH_SIZE]
            batch_results = await self._embed_batch(batch)
            results.extend(batch_results)
        return results

    async def embed_single(self, text: str) -> EmbeddingResult:
        """Embed a single text string."""
        results = await self._embed_batch([text])
        return results[0]

    async def _embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Call DashScope API with retry logic."""
        import dashscope
        from http import HTTPStatus

        max_retries = 3
        for attempt in range(max_retries):
            try:
                resp = dashscope.TextEmbedding.call(
                    model=self.model,
                    input=texts,
                    dimension=self.dimensions,
                    api_key=self.api_key,
                )
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning(
                        "Embedding API error, retrying in %ds (attempt %d/%d): %s",
                        wait, attempt + 1, max_retries, e,
                    )
                    await asyncio.sleep(wait)
                    continue
                raise EmbeddingError(f"Embedding API failed after {max_retries} attempts", cause=e) from e

            if resp.status_code == HTTPStatus.OK:
                return [
                    EmbeddingResult(
                        embedding=item["embedding"],
                        model=self.model,
                        tokens_used=resp.usage.get("total_tokens", 0),
                        metadata={"index": i},
                    )
                    for i, item in enumerate(resp.output["embeddings"])
                ]
            elif resp.status_code == 429:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning("Rate limited, retrying in %ds", wait)
                    await asyncio.sleep(wait)
                    continue
                raise EmbeddingError(f"Rate limit exceeded: {resp.message}")
            elif resp.status_code in (401, 403):
                raise EmbeddingError(f"Authentication failed: {resp.message}")
            else:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    await asyncio.sleep(wait)
                    continue
                raise EmbeddingError(f"Unexpected API error ({resp.status_code}): {resp.message}")

        raise EmbeddingError("Unreachable: all retries exhausted")
```

- [ ] **Step 5: 运行测试验证通过**

Run: `pytest tests/test_rag/test_embedder.py::TestDashScopeEmbedderInit -v`
Expected: PASS

- [ ] **Step 6: 添加 embed 方法测试（mock API）**

补全 `tests/test_rag/test_embedder.py`:

```python
class TestDashScopeEmbedSingle:
    """Test embed_single with mocked DashScope API."""

    @pytest.fixture
    def mock_response(self):
        """Create a mock DashScope response."""
        mock = MagicMock()
        mock.status_code = 200
        mock.output = {"embeddings": [{"embedding": [0.1] * 1024, "text_index": 0}]}
        mock.usage = {"total_tokens": 5}
        return mock

    @patch("dashscope.TextEmbedding.call")
    def test_embed_single_returns_embedding_result(self, mock_call, mock_response):
        """Should return EmbeddingResult with correct embedding."""
        mock_call.return_value = mock_response
        embedder = DashScopeEmbedder(api_key="sk-test")
        result = asyncio.run(embedder.embed_single("hello"))
        assert isinstance(result, EmbeddingResult)
        assert len(result.embedding) == 1024
        assert result.model == "text-embedding-v3"

    @patch("dashscope.TextEmbedding.call")
    def test_embed_single_tokens_usage(self, mock_call, mock_response):
        """Should report correct token usage."""
        mock_response.usage = {"total_tokens": 8}
        mock_call.return_value = mock_response
        embedder = DashScopeEmbedder(api_key="sk-test")
        result = asyncio.run(embedder.embed_single("hello world"))
        assert result.tokens_used == 8

    @patch("dashscope.TextEmbedding.call")
    def test_embed_with_custom_dimensions(self, mock_call, mock_response):
        """Should pass custom dimensions."""
        mock_response.output["embeddings"][0]["embedding"] = [0.1] * 768
        mock_call.return_value = mock_response
        embedder = DashScopeEmbedder(api_key="sk-test", dimensions=768)
        result = asyncio.run(embedder.embed_single("hello"))
        assert len(result.embedding) == 768
        call_args = mock_call.call_args[1]
        assert call_args.get("dimension") == 768


class TestDashScopeEmbedBatch:
    """Test batch embedding with mocked DashScope API."""

    @pytest.fixture
    def mock_response_3(self):
        mock = MagicMock()
        mock.status_code = 200
        mock.output = {
            "embeddings": [
                {"embedding": [0.1] * 1024, "text_index": 0},
                {"embedding": [0.2] * 1024, "text_index": 1},
                {"embedding": [0.3] * 1024, "text_index": 2},
            ]
        }
        mock.usage = {"total_tokens": 15}
        return mock

    @patch("dashscope.TextEmbedding.call")
    def test_embed_list_returns_multiple_results(self, mock_call, mock_response_3):
        """Should return one EmbeddingResult per input text."""
        mock_call.return_value = mock_response_3
        embedder = DashScopeEmbedder(api_key="sk-test")
        results = asyncio.run(embedder.embed(["a", "b", "c"]))
        assert len(results) == 3
        assert results[0].embedding == [0.1] * 1024
        assert results[2].embedding == [0.3] * 1024

    @patch("dashscope.TextEmbedding.call")
    def test_embed_str_returns_single_result_list(self, mock_call, mock_response_3):
        """embed('text') should return list with one result."""
        mock_response_3.output["embeddings"] = [mock_response_3.output["embeddings"][0]]
        mock_call.return_value = mock_response_3
        embedder = DashScopeEmbedder(api_key="sk-test")
        results = asyncio.run(embedder.embed("single"))
        assert len(results) == 1
```

- [ ] **Step 7: 运行全部 embedder 测试**

Run: `pytest tests/test_rag/test_embedder.py -v`
Expected: 7 passed

- [ ] **Step 8: Commit**

```bash
git add tests/test_rag/conftest.py tests/test_rag/test_embedder.py src/lukawi/rag/embedder.py
git commit -m "feat(rag): implement DashScopeEmbedder with retry, batch, and single embedding"
```

---

### Task 4: 文档加载器

**Files:**
- Create: `src/lukawi/rag/document.py`
- Create: `tests/test_rag/test_document.py`

- [ ] **Step 1: 写 failing test — 加载 txt 文件**

`tests/test_rag/test_document.py`:

```python
"""Tests for DocumentLoader."""

from __future__ import annotations

import pytest
from pathlib import Path

from lukawi.rag.document import DocumentLoader, DocumentChunk
from lukawi.rag.exceptions import DocumentLoadError


class TestDocumentLoaderInit:
    """Test loader initialization."""

    def test_default_chunk_size(self):
        loader = DocumentLoader()
        assert loader.chunk_size == 500

    def test_custom_chunk_size(self):
        loader = DocumentLoader(chunk_size=300, chunk_overlap=30)
        assert loader.chunk_size == 300
        assert loader.chunk_overlap == 30


class TestLoadFile:
    """Test loading and chunking files."""

    def test_load_txt_returns_chunks(self, sample_text_file):
        """Should load a .txt file and return at least one chunk."""
        loader = DocumentLoader()
        chunks = loader.load_file(sample_text_file)
        assert len(chunks) >= 1
        assert all(isinstance(c, DocumentChunk) for c in chunks)

    def test_txt_chunk_contains_content(self, sample_text_file):
        """Chunk content should contain original file text."""
        loader = DocumentLoader()
        chunks = loader.load_file(sample_text_file)
        assert "Lukawi Agent" in chunks[0].content

    def test_txt_chunk_has_metadata(self, sample_text_file):
        """Each chunk should have source_path and chunk_index."""
        loader = DocumentLoader()
        chunks = loader.load_file(sample_text_file)
        assert chunks[0].source_path == str(sample_text_file)
        assert chunks[0].chunk_index == 0

    def test_load_md_returns_chunks(self, sample_markdown_file):
        """Should load .md files same as .txt."""
        loader = DocumentLoader()
        chunks = loader.load_file(sample_markdown_file)
        assert len(chunks) >= 1

    def test_load_nonexistent_file_raises(self, temp_dir):
        """Should raise DocumentLoadError for missing files."""
        loader = DocumentLoader()
        with pytest.raises(DocumentLoadError, match="不存在"):
            loader.load_file(temp_dir / "nonexistent.txt")

    def test_load_directory_returns_nonexistent(self, temp_dir):
        """load_directory on missing path raises error."""
        loader = DocumentLoader()
        with pytest.raises(DocumentLoadError):
            loader.load_directory(temp_dir / "no_such_dir")
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_rag/test_document.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现 DocumentLoader**

`src/lukawi/rag/document.py`:

```python
"""Document loader with sentence-boundary chunking and encoding fallback."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path

from lukawi.rag.exceptions import DocumentLoadError


@dataclass
class DocumentChunk:
    """A text chunk from a loaded document."""
    id: str
    content: str
    source_path: str
    chunk_index: int
    metadata: dict = field(default_factory=dict)


class DocumentLoader:
    """Load text/markdown files and split into overlapping chunks.

    Chunking strategy:
    - Splits on sentence boundaries (。！？\\n\\n)
    - chunk_size: max tokens per chunk (approximate)
    - chunk_overlap: tokens to overlap between adjacent chunks
    """

    ENCODINGS = ["utf-8", "gbk", "gb2312", "latin-1"]

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def load_file(self, path: str | Path) -> list[DocumentChunk]:
        """Load a single file and split into chunks."""
        path = Path(path)
        if not path.exists():
            raise DocumentLoadError(f"文件不存在: {path}")
        if not path.is_file():
            raise DocumentLoadError(f"不是文件: {path}")

        text = self._read_file(path)
        return self._split_text(text, str(path))

    def load_directory(self, path: str | Path) -> list[DocumentChunk]:
        """Load all .txt/.md/.markdown files from a directory (non-recursive)."""
        path = Path(path)
        if not path.exists() or not path.is_dir():
            raise DocumentLoadError(f"目录不存在: {path}")

        supported = {".txt", ".md", ".markdown"}
        chunks: list[DocumentChunk] = []
        for file_path in sorted(path.iterdir()):
            if file_path.suffix.lower() in supported and file_path.is_file():
                chunks.extend(self.load_file(file_path))
        return chunks

    def _read_file(self, path: Path) -> str:
        """Read file with encoding fallback chain."""
        raw = path.read_bytes()
        for encoding in self.ENCODINGS:
            try:
                return raw.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        return raw.decode("latin-1")

    def _split_text(self, text: str, source: str) -> list[DocumentChunk]:
        """Split text on sentence boundaries with sliding-window overlap.

        Uses paragraph breaks (\\n\\n) as primary boundaries,
        then sentence-ending punctuation as secondary.
        """
        # Step 1: Split into paragraph-level segments
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        # Step 2: Within each paragraph, split long sentences
        segments: list[str] = []
        for para in paragraphs:
            if self._estimate_tokens(para) <= self.chunk_size:
                segments.append(para)
            else:
                # Further split on sentence boundaries
                sentences = self._split_sentences(para)
                for sent in sentences:
                    segments.append(sent)

        # Step 3: Merge small segments, split oversized ones with overlap
        chunks: list[DocumentChunk] = []
        current = ""
        index = 0
        for seg in segments:
            if not current:
                current = seg
                continue
            combined = current + "\n" + seg
            if self._estimate_tokens(combined) <= self.chunk_size:
                current = combined
            else:
                chunks.append(self._make_chunk(current, source, index))
                index += 1
                # Add overlap from previous chunk tail
                overlap = self._get_overlap(current)
                current = overlap + "\n" + seg if overlap else seg

        if current:
            chunks.append(self._make_chunk(current, source, index))

        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        """Split text on Chinese/English sentence boundaries."""
        import re
        # Split on 。！？\n followed by optional whitespace
        parts = re.split(r"(?<=[。！？\n])\s*", text)
        return [p.strip() for p in parts if p.strip()]

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation: ~1.5 chars per token for Chinese, ~4 for English."""
        chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        other_chars = len(text) - chinese_chars
        return int(chinese_chars / 1.5 + other_chars / 4)

    def _get_overlap(self, text: str) -> str:
        """Extract tail portion for overlap between chunks."""
        sentences = self._split_sentences(text)
        overlap = ""
        for s in reversed(sentences):
            candidate = s + ("\n" + overlap if overlap else "")
            if self._estimate_tokens(candidate) <= self.chunk_overlap:
                overlap = candidate
            else:
                break
        return overlap

    def _make_chunk(self, content: str, source: str, index: int) -> DocumentChunk:
        return DocumentChunk(
            id=str(uuid.uuid4()),
            content=content.strip(),
            source_path=source,
            chunk_index=index,
        )
```

- [ ] **Step 4: 运行基础测试**

Run: `pytest tests/test_rag/test_document.py -v`
Expected: 7 passed

- [ ] **Step 5: 添加编码回退和边界测试**

补全 `tests/test_rag/test_document.py`:

```python
class TestEncodingFallback:
    """Test multi-encoding file reading."""

    def test_read_gbk_encoded_file(self, gbk_encoded_file):
        """GBK-encoded Chinese file should decode correctly."""
        loader = DocumentLoader()
        chunks = loader.load_file(gbk_encoded_file)
        assert "中文技术文档" in chunks[0].content

    def test_read_utf8_with_bom(self, temp_dir):
        """UTF-8 BOM should be handled."""
        path = temp_dir / "bom.txt"
        path.write_bytes(b"\xef\xbb\xbfhello world\n")
        loader = DocumentLoader()
        chunks = loader.load_file(path)
        assert "hello world" in chunks[0].content


class TestChunkBoundaries:
    """Test chunk splitting behavior."""

    def test_small_file_single_chunk(self, temp_dir):
        """A small file should produce exactly one chunk."""
        path = temp_dir / "small.txt"
        path.write_text("hello", encoding="utf-8")
        loader = DocumentLoader()
        chunks = loader.load_file(path)
        assert len(chunks) == 1

    def test_chunks_have_unique_ids(self, sample_text_file):
        """Each chunk should have a unique ID."""
        loader = DocumentLoader(chunk_size=50, chunk_overlap=10)
        chunks = loader.load_file(sample_text_file)
        ids = {c.id for c in chunks}
        assert len(ids) == len(chunks)

    def test_chunks_indexed_sequentially(self, sample_text_file):
        """Chunk indices should be sequential starting from 0."""
        loader = DocumentLoader(chunk_size=50, chunk_overlap=10)
        chunks = loader.load_file(sample_text_file)
        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))
```

- [ ] **Step 6: 运行全部 document 测试**

Run: `pytest tests/test_rag/test_document.py -v`
Expected: 12 passed

- [ ] **Step 7: Commit**

```bash
git add src/lukawi/rag/document.py tests/test_rag/test_document.py
git commit -m "feat(rag): implement DocumentLoader with sentence-boundary chunking and encoding fallback"
```

---

### Task 5: ChromaDB 向量存储

**Files:**
- Create: `src/lukawi/rag/store.py`
- Create: `tests/test_rag/test_store.py`

- [ ] **Step 1: 写 failing test**

`tests/test_rag/test_store.py`:

```python
"""Tests for VectorStore with ChromaDB."""

from __future__ import annotations

import asyncio
import pytest

from lukawi.rag.store import VectorStore, SearchResult
from lukawi.rag.document import DocumentChunk


class TestVectorStoreInit:
    """Test store initialization and lifecycle."""

    def test_init_creates_store(self, temp_dir):
        """Should create a VectorStore with persist_dir."""
        store = VectorStore(persist_dir=str(temp_dir / "chroma_test"))
        assert store.persist_dir == str(temp_dir / "chroma_test")

    def test_initialize_creates_collections(self, temp_dir):
        """initialize() should create docs and conversations collections."""
        store = VectorStore(persist_dir=str(temp_dir / "chroma_test"))
        asyncio.run(store.initialize())
        assert store.collection_docs is not None
        assert store.collection_conv is not None
        assert store.collection_docs.name == "documents"
        assert store.collection_conv.name == "conversations"
        store.close()

    def test_close_cleans_up(self, temp_dir):
        """close() should clean up resources."""
        store = VectorStore(persist_dir=str(temp_dir / "chroma_test"))
        asyncio.run(store.initialize())
        store.close()
        assert store.client is None


class TestAddAndSearchDocuments:
    """Test document CRUD operations."""

    @pytest.fixture
    def store(self, temp_dir):
        """Create initialized store."""
        s = VectorStore(persist_dir=str(temp_dir / "chroma_test2"))
        asyncio.run(s.initialize())
        yield s
        s.close()

    @pytest.fixture
    def sample_chunks(self):
        return [
            DocumentChunk(
                id="c1", content="Lukawi Agent 是一个 AI 框架",
                source_path="/tmp/test.txt", chunk_index=0,
            ),
            DocumentChunk(
                id="c2", content="它支持 RAG 检索增强生成",
                source_path="/tmp/test.txt", chunk_index=1,
            ),
        ]

    def test_add_documents_returns_ids(self, store, sample_chunks):
        """add_documents should return chunk IDs."""
        ids = asyncio.run(store.add_documents(sample_chunks))
        assert len(ids) == 2
        assert "c1" in ids

    def test_delete_document_by_source(self, store, sample_chunks):
        """delete_document should remove chunks by source path."""
        asyncio.run(store.add_documents(sample_chunks))
        deleted = asyncio.run(store.delete_document("/tmp/test.txt"))
        assert deleted == 2

    def test_delete_nonexistent_document_returns_zero(self, store):
        """Deleting unknown path should return 0."""
        deleted = asyncio.run(store.delete_document("/tmp/never_uploaded.txt"))
        assert deleted == 0
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_rag/test_store.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现 VectorStore**

`src/lukawi/rag/store.py`:

```python
"""ChromaDB vector store with documents and conversations collections."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import chromadb
from chromadb.config import Settings

from lukawi.rag.document import DocumentChunk
from lukawi.rag.exceptions import StorageError

logger = logging.getLogger("lukawi.rag.store")


@dataclass
class SearchResult:
    """A single search result from vector retrieval."""
    chunk_id: str
    content: str
    score: float
    metadata: dict = field(default_factory=dict)


class VectorStore:
    """ChromaDB wrapper managing two collections: documents and conversations."""

    def __init__(self, persist_dir: str = "./chroma_db") -> None:
        self.persist_dir = persist_dir
        self.client: chromadb.ClientAPI | None = None
        self.collection_docs: chromadb.Collection | None = None
        self.collection_conv: chromadb.Collection | None = None

    async def initialize(self) -> None:
        """Create/connect ChromaDB client and collections."""
        try:
            self.client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
        except Exception as e:
            raise StorageError(f"Failed to initialize ChromaDB at {self.persist_dir}", cause=e) from e

        self.collection_docs = self.client.get_or_create_collection(
            name="documents",
            metadata={"description": "Uploaded document chunks"},
        )
        self.collection_conv = self.client.get_or_create_collection(
            name="conversations",
            metadata={"description": "Conversation history embeddings"},
        )
        logger.info("VectorStore initialized at %s (2 collections)", self.persist_dir)

    async def add_documents(self, chunks: list[DocumentChunk]) -> list[str]:
        """Add document chunks to the documents collection."""
        if not self.collection_docs:
            raise StorageError("Store not initialized")
        if not chunks:
            return []

        ids = [c.id for c in chunks]
        documents = [c.content for c in chunks]
        metadatas = [
            {
                "source_path": c.source_path,
                "chunk_index": c.chunk_index,
                **c.metadata,
            }
            for c in chunks
        ]
        self.collection_docs.add(ids=ids, documents=documents, metadatas=metadatas)
        logger.info("Added %d document chunks", len(chunks))
        return ids

    async def search_documents(
        self, query_text: str, limit: int = 5
    ) -> list[SearchResult]:
        """Semantic search over documents collection."""
        if not self.collection_docs:
            raise StorageError("Store not initialized")

        results = self.collection_docs.query(query_texts=[query_text], n_results=limit)
        return self._parse_results(results)

    async def delete_document(self, source_path: str) -> int:
        """Delete all chunks belonging to a specific source document."""
        if not self.collection_docs:
            raise StorageError("Store not initialized")

        existing = self.collection_docs.get(
            where={"source_path": source_path}
        )
        if not existing["ids"]:
            return 0

        self.collection_docs.delete(ids=existing["ids"])
        count = len(existing["ids"])
        logger.info("Deleted %d chunks for %s", count, source_path)
        return count

    async def add_conversation(self, content: str, metadata: dict | None = None) -> str:
        """Add a conversation summary to conversations collection."""
        if not self.collection_conv:
            raise StorageError("Store not initialized")

        import uuid
        conv_id = str(uuid.uuid4())
        self.collection_conv.add(
            ids=[conv_id],
            documents=[content],
            metadatas=[metadata or {}],
        )
        return conv_id

    async def search_conversations(
        self, query_text: str, user_id: str = "default", limit: int = 5
    ) -> list[SearchResult]:
        """Semantic search over conversations collection, scoped by user_id."""
        if not self.collection_conv:
            raise StorageError("Store not initialized")

        results = self.collection_conv.query(
            query_texts=[query_text],
            n_results=limit,
            where={"user_id": user_id},
        )
        return self._parse_results(results)

    async def delete_conversation(self, conv_id: str) -> bool:
        """Delete a specific conversation entry."""
        if not self.collection_conv:
            raise StorageError("Store not initialized")
        existing = self.collection_conv.get(ids=[conv_id])
        if not existing["ids"]:
            return False
        self.collection_conv.delete(ids=[conv_id])
        return True

    def close(self) -> None:
        """Close the ChromaDB client."""
        self.client = None
        self.collection_docs = None
        self.collection_conv = None

    def _parse_results(self, results: dict) -> list[SearchResult]:
        """Convert ChromaDB query results to SearchResult list."""
        if not results.get("ids") or not results["ids"][0]:
            return []
        return [
            SearchResult(
                chunk_id=results["ids"][0][i],
                content=results["documents"][0][i],
                score=results.get("distances", [[1.0]])[0][i],
                metadata=results.get("metadatas", [[{}]])[0][i],
            )
            for i in range(len(results["ids"][0]))
        ]
```

- [ ] **Step 4: 运行 store 测试**

Run: `pytest tests/test_rag/test_store.py -v`
Expected: 6 passed

- [ ] **Step 5: 添加 conversations 测试**

补全 `tests/test_rag/test_store.py`:

```python
class TestConversations:
    """Test conversation operations."""

    @pytest.fixture
    def store(self, temp_dir):
        s = VectorStore(persist_dir=str(temp_dir / "chroma_conv_test"))
        asyncio.run(s.initialize())
        yield s
        s.close()

    def test_add_conversation_returns_id(self, store):
        """Should return a UUID string."""
        conv_id = asyncio.run(
            store.add_conversation("用户询问了天气", {"user_id": "default"})
        )
        assert len(conv_id) == 36  # UUID4 format
        assert "-" in conv_id

    def test_delete_conversation_true_for_existing(self, store):
        """Should return True when deleting an existing conversation."""
        conv_id = asyncio.run(
            store.add_conversation("test content", {"user_id": "default"})
        )
        result = asyncio.run(store.delete_conversation(conv_id))
        assert result is True

    def test_delete_conversation_false_for_nonexistent(self, store):
        """Should return False for non-existent ID."""
        result = asyncio.run(store.delete_conversation("nonexistent-id"))
        assert result is False
```

- [ ] **Step 6: 运行全部 store 测试**

Run: `pytest tests/test_rag/test_store.py -v`
Expected: 9 passed

- [ ] **Step 7: Commit**

```bash
git add src/lukawi/rag/store.py tests/test_rag/test_store.py
git commit -m "feat(rag): implement VectorStore with ChromaDB for documents and conversations"
```

---

### Task 6: 检索器

**Files:**
- Create: `src/lukawi/rag/retriever.py`
- Create: `tests/test_rag/test_retriever.py`

- [ ] **Step 1: 写 failing test**

`tests/test_rag/test_retriever.py`:

```python
"""Tests for Retriever."""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import MagicMock, patch

from lukawi.rag.retriever import Retriever
from lukawi.rag.store import SearchResult


class TestRetriever:
    """Test unified retrieval across both collections."""

    @pytest.fixture
    def mock_store(self):
        store = MagicMock()
        store.search_documents = MagicMock()
        store.search_conversations = MagicMock()
        return store

    @pytest.fixture
    def mock_embedder(self):
        return MagicMock()

    def test_retrieve_documents_delegates(self, mock_store, mock_embedder):
        """retrieve_documents should call store.search_documents."""
        mock_store.search_documents.return_value = asyncio.Future()
        mock_store.search_documents.return_value.set_result([
            SearchResult(chunk_id="c1", content="test", score=0.9, metadata={})
        ])
        retriever = Retriever(store=mock_store, embedder=mock_embedder)
        results = asyncio.run(retriever.retrieve_documents("hello", limit=3))
        mock_store.search_documents.assert_called_once_with("hello", limit=3)
        assert len(results) == 1
        assert results[0].chunk_id == "c1"

    def test_retrieve_conversations_delegates(self, mock_store, mock_embedder):
        """retrieve_conversations should call store.search_conversations."""
        mock_store.search_conversations.return_value = asyncio.Future()
        mock_store.search_conversations.return_value.set_result([
            SearchResult(chunk_id="cv1", content="history", score=0.8, metadata={"user_id": "u1"})
        ])
        retriever = Retriever(store=mock_store, embedder=mock_embedder)
        results = asyncio.run(
            retriever.retrieve_conversations("hello", user_id="u1", limit=3)
        )
        mock_store.search_conversations.assert_called_once_with("hello", "u1", limit=3)
        assert results[0].chunk_id == "cv1"

    def test_retrieve_all_merges_and_sorts(self, mock_store, mock_embedder):
        """retrieve() should merge docs and conversations, sorted by score descending."""
        async def mock_docs(*args, **kwargs):
            return [
                SearchResult(chunk_id="d1", content="doc result", score=0.7, metadata={}),
                SearchResult(chunk_id="d2", content="doc result 2", score=0.3, metadata={}),
            ]
        async def mock_convs(*args, **kwargs):
            return [
                SearchResult(chunk_id="cv1", content="conv result", score=0.9, metadata={}),
            ]
        mock_store.search_documents = mock_docs
        mock_store.search_conversations = mock_convs

        retriever = Retriever(store=mock_store, embedder=mock_embedder)
        results = asyncio.run(retriever.retrieve("query", sources=["docs", "conversations"]))
        # Sorted by score desc: cv1(0.9), d1(0.7), d2(0.3)
        assert results[0].chunk_id == "cv1"
        assert results[1].chunk_id == "d1"
        assert results[2].chunk_id == "d2"

    def test_retrieve_source_filter(self, mock_store, mock_embedder):
        """retrieve with sources=['docs'] should only search documents."""
        async def mock_docs(*args, **kwargs):
            return [SearchResult(chunk_id="d1", content="x", score=0.5, metadata={})]
        mock_store.search_documents = mock_docs
        retriever = Retriever(store=mock_store, embedder=mock_embedder)
        results = asyncio.run(retriever.retrieve("query", sources=["docs"]))
        assert len(results) == 1
        mock_store.search_conversations.assert_not_called()
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_rag/test_retriever.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 Retriever**

`src/lukawi/rag/retriever.py`:

```python
"""Unified retriever that aggregates document and conversation search."""

from __future__ import annotations

import logging

from lukawi.rag.store import VectorStore, SearchResult
from lukawi.rag.embedder import DashScopeEmbedder

logger = logging.getLogger("lukawi.rag.retriever")


class Retriever:
    """Top-level retrieval interface combining document and conversation search."""

    def __init__(
        self,
        store: VectorStore,
        embedder: DashScopeEmbedder,
    ) -> None:
        self.store = store
        self.embedder = embedder

    async def retrieve(
        self,
        query: str,
        user_id: str = "default",
        sources: list[str] | None = None,
        limit_per_source: int = 5,
    ) -> list[SearchResult]:
        """Search across specified sources, merge and sort by relevance.

        Args:
            query: Natural language search query.
            user_id: User ID for conversation scoping.
            sources: Which collections to search. None = all.
            limit_per_source: Max results per source.

        Returns:
            Combined and sorted SearchResult list (highest score first).
        """
        if sources is None:
            sources = ["docs", "conversations"]

        all_results: list[SearchResult] = []

        if "docs" in sources:
            doc_results = await self.retrieve_documents(query, limit=limit_per_source)
            all_results.extend(doc_results)

        if "conversations" in sources:
            conv_results = await self.retrieve_conversations(
                query, user_id=user_id, limit=limit_per_source
            )
            all_results.extend(conv_results)

        # Sort by score descending (lower ChromaDB distance = higher relevance)
        # ChromaDB returns cosine distance: lower is better
        all_results.sort(key=lambda r: r.score)
        return all_results

    async def retrieve_documents(
        self, query: str, limit: int = 5
    ) -> list[SearchResult]:
        """Search only the documents collection."""
        return await self.store.search_documents(query_text=query, limit=limit)

    async def retrieve_conversations(
        self, query: str, user_id: str = "default", limit: int = 5
    ) -> list[SearchResult]:
        """Search only the conversations collection."""
        return await self.store.search_conversations(
            query_text=query, user_id=user_id, limit=limit
        )
```

- [ ] **Step 4: 运行全部 retriever 测试**

Run: `pytest tests/test_rag/test_retriever.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/lukawi/rag/retriever.py tests/test_rag/test_retriever.py
git commit -m "feat(rag): implement Retriever with unified multi-source search and score sorting"
```

---

### Task 7: RAGManager 总管

**Files:**
- Create: `src/lukawi/rag/manager.py`
- Create: `tests/test_rag/test_manager.py`

- [ ] **Step 1: 写 failing test**

`tests/test_rag/test_manager.py`:

```python
"""Tests for RAGManager."""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

from lukawi.rag.manager import RAGManager
from lukawi.rag.exceptions import DocumentLoadError


class TestRAGManagerLifecycle:
    """Test init, initialize, close."""

    @pytest.fixture
    def mock_embedder(self):
        return MagicMock()

    @pytest.fixture
    def mock_store(self):
        store = MagicMock()
        store.initialize = AsyncMock()
        store.close = MagicMock()
        return store

    def test_init_stores_dependencies(self, mock_embedder, mock_store):
        mgr = RAGManager(embedder=mock_embedder, store=mock_store)
        assert mgr.embedder is mock_embedder
        assert mgr.store is mock_store

    def test_initialize_delegates_to_store(self, mock_embedder, mock_store):
        mgr = RAGManager(embedder=mock_embedder, store=mock_store)
        asyncio.run(mgr.initialize())
        mock_store.initialize.assert_awaited_once()


class TestUploadDocument:
    """Test file upload flow."""

    @pytest.fixture
    def mock_embedder(self):
        return MagicMock()

    @pytest.fixture
    def mock_store(self):
        store = MagicMock()
        store.initialize = AsyncMock()
        store.add_documents = AsyncMock(return_value=["c1", "c2"])
        store.delete_document = AsyncMock(return_value=0)
        return store

    def test_upload_rejects_unsupported_format(self, mock_embedder, mock_store, temp_dir):
        """Non-txt/md files should be rejected."""
        path = temp_dir / "image.png"
        path.write_bytes(b"\x89PNG\x0d\x0a")
        mgr = RAGManager(embedder=mock_embedder, store=mock_store)
        with pytest.raises(DocumentLoadError, match="不支持"):
            asyncio.run(mgr.upload_document(path))

    def test_upload_rejects_oversized_file(self, mock_embedder, mock_store, temp_dir):
        """Files > 10MB should be rejected."""
        path = temp_dir / "big.txt"
        # Create a file that reports >10MB in size
        mgr = RAGManager(embedder=mock_embedder, store=mock_store)
        with patch.object(Path, "stat") as mock_stat:
            mock_stat.return_value.st_size = 11 * 1024 * 1024
            path.touch()
            with pytest.raises(DocumentLoadError, match="10MB"):
                asyncio.run(mgr.upload_document(path))

    def test_upload_success_returns_chunk_count(self, mock_embedder, mock_store, sample_text_file):
        """Successful upload should return chunk count and path info."""
        mock_store.delete_document.return_value = asyncio.Future()
        mock_store.delete_document.return_value.set_result(0)
        mock_store.add_documents.return_value = asyncio.Future()
        mock_store.add_documents.return_value.set_result(["c1"])

        mgr = RAGManager(embedder=mock_embedder, store=mock_store)
        result = asyncio.run(mgr.upload_document(sample_text_file))
        assert result["chunks"] == 1
        assert result["filename"] == "sample.txt"
        assert "path" in result

    def test_list_documents_after_upload(self, mock_embedder, mock_store, sample_text_file):
        """list_documents should reflect uploaded files."""
        mock_store.delete_document.return_value = asyncio.Future()
        mock_store.delete_document.return_value.set_result(0)
        mock_store.add_documents.return_value = asyncio.Future()
        mock_store.add_documents.return_value.set_result(["c1", "c2"])
        mock_store.collection_docs = MagicMock()
        mock_store.collection_docs.get.return_value = {
            "ids": ["c1", "c2"],
            "metadatas": [
                {"source_path": str(sample_text_file)},
                {"source_path": str(sample_text_file)},
            ],
        }

        mgr = RAGManager(embedder=mock_embedder, store=mock_store)
        asyncio.run(mgr.upload_document(sample_text_file))
        docs = asyncio.run(mgr.list_documents())
        assert len(docs) == 1
        assert docs[0]["filename"] == "sample.txt"
        assert docs[0]["chunks"] == 2
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_rag/test_manager.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 RAGManager**

`src/lukawi/rag/manager.py`:

```python
"""RAG lifecycle manager — orchestrate embedding, storage, and retrieval."""

from __future__ import annotations

import logging
from pathlib import Path

from lukawi.rag.embedder import DashScopeEmbedder
from lukawi.rag.store import VectorStore, SearchResult
from lukawi.rag.document import DocumentLoader, DocumentChunk
from lukawi.rag.retriever import Retriever
from lukawi.rag.exceptions import DocumentLoadError

logger = logging.getLogger("lukawi.rag.manager")

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class RAGManager:
    """Orchestrates document upload, conversation indexing, and retrieval."""

    def __init__(
        self,
        embedder: DashScopeEmbedder,
        store: VectorStore,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> None:
        self.embedder = embedder
        self.store = store
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.retriever: Retriever | None = None

    async def initialize(self) -> None:
        """Initialize store and retriever."""
        await self.store.initialize()
        self.retriever = Retriever(store=self.store, embedder=self.embedder)
        logger.info("RAGManager initialized")

    async def close(self) -> None:
        """Close store resources."""
        self.store.close()
        self.retriever = None
        logger.info("RAGManager closed")

    async def upload_document(self, path: str | Path) -> dict:
        """Upload a document: validate → load → chunk → store.

        If a document with the same path already exists, it is replaced.
        """
        path = Path(path)
        self._validate_file(path)

        # Remove old chunks if re-uploading
        existing = await self.store.delete_document(str(path))

        # Load and chunk
        loader = DocumentLoader(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        chunks = loader.load_file(path)

        # Store
        ids = await self.store.add_documents(chunks)

        logger.info(
            "Uploaded %s: %d chunks (replaced: %s)",
            path.name, len(chunks), existing > 0,
        )
        return {
            "path": str(path),
            "filename": path.name,
            "chunks": len(chunks),
            "replaced": existing > 0,
        }

    async def search(
        self,
        query: str,
        user_id: str = "default",
        sources: list[str] | None = None,
        limit: int = 5,
    ) -> list[SearchResult]:
        """Unified search across documents and conversations."""
        if not self.retriever:
            raise DocumentLoadError("RAGManager not initialized")
        return await self.retriever.retrieve(
            query=query,
            user_id=user_id,
            sources=sources,
            limit_per_source=limit,
        )

    async def index_conversation(
        self,
        content: str,
        user_id: str = "default",
        metadata: dict | None = None,
    ) -> str:
        """Index a conversation summary into the conversations collection."""
        meta = metadata or {}
        meta["user_id"] = user_id
        meta["type"] = "conversation_summary"
        conv_id = await self.store.add_conversation(content=content, metadata=meta)
        logger.debug("Indexed conversation %s for user %s", conv_id, user_id)
        return conv_id

    async def list_documents(self) -> list[dict]:
        """List all uploaded documents with their metadata."""
        if not self.store.collection_docs:
            return []
        results = self.store.collection_docs.get(include=["metadatas"])
        if not results or not results.get("ids"):
            return []

        # Group by source_path
        seen: dict[str, dict] = {}
        for meta in results["metadatas"]:
            source = meta.get("source_path", "unknown")
            if source not in seen:
                seen[source] = {
                    "path": source,
                    "filename": Path(source).name,
                    "chunks": 1,
                }
            else:
                seen[source]["chunks"] += 1
        return list(seen.values())

    async def remove_document(self, source_path: str) -> int:
        """Remove all chunks belonging to a document."""
        return await self.store.delete_document(source_path)

    def _validate_file(self, path: Path) -> None:
        """Validate file before upload."""
        if not path.exists():
            raise DocumentLoadError(f"文件不存在: {path}")
        if not path.is_file():
            raise DocumentLoadError(f"不是文件: {path}")
        if path.suffix.lower() not in (".txt", ".md", ".markdown"):
            raise DocumentLoadError(
                f"不支持的文件格式: {path.suffix}，当前支持 .txt / .md"
            )
        if path.stat().st_size > MAX_FILE_SIZE:
            raise DocumentLoadError(
                f"文件过大（{path.stat().st_size / 1024 / 1024:.1f}MB），请限制在 10MB 以内"
            )
```

- [ ] **Step 4: 运行 manager 测试**

Run: `pytest tests/test_rag/test_manager.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/lukawi/rag/manager.py tests/test_rag/test_manager.py
git commit -m "feat(rag): implement RAGManager with upload, search, conversation indexing, and document listing"
```

---

### Task 8: RAG 工具注册

**Files:**
- Create: `src/lukawi/tools/builtin/rag_search.py`
- Modify: `src/lukawi/tools/builtin/__init__.py`

- [ ] **Step 1: 创建三个工具定义**

`src/lukawi/tools/builtin/rag_search.py`:

```python
"""RAG tools: semantic search, file upload, document listing."""

from __future__ import annotations

from pathlib import Path

from lukawi.tools.base import (
    ToolDefinition,
    ToolResult,
    ToolParameter,
    ToolParameterType,
)
from lukawi.tools.registry import ToolRegistry


RAG_SEARCH_TOOL = ToolDefinition(
    name="rag_search",
    description=(
        "语义搜索本地知识库。可以搜索之前上传的文档内容（txt/markdown）"
        "以及历史对话记录。用于：查找文档中的信息、回忆之前的对话内容。"
    ),
    parameters=[
        ToolParameter(
            name="query",
            type=ToolParameterType.STRING,
            description="自然语言搜索查询，描述你想找什么内容",
        ),
        ToolParameter(
            name="source",
            type=ToolParameterType.STRING,
            description="搜索来源：'docs' 只搜文档, 'conversations' 只搜对话, 'all' 全部",
            required=False,
            default="all",
        ),
        ToolParameter(
            name="limit",
            type=ToolParameterType.INTEGER,
            description="最多返回多少条结果",
            required=False,
            default=5,
        ),
    ],
    category="rag",
    tags=["rag", "search", "knowledge", "documents", "memory"],
)

RAG_UPLOAD_TOOL = ToolDefinition(
    name="rag_upload",
    description=(
        "上传本地文件到知识库。上传后文件内容会被自动分块、向量化，"
        "之后可以通过 rag_search 检索。支持 .txt 和 .md 文件。"
    ),
    parameters=[
        ToolParameter(
            name="path",
            type=ToolParameterType.STRING,
            description="要上传的文件路径（支持 .txt 或 .md 文件）",
        ),
    ],
    category="rag",
    tags=["rag", "upload", "knowledge", "documents"],
)

RAG_LIST_TOOL = ToolDefinition(
    name="rag_list",
    description="列出知识库中所有已上传的文档及其基本信息。",
    parameters=[],
    category="rag",
    tags=["rag", "list", "documents", "knowledge"],
)


def register_rag_tools(
    registry: ToolRegistry,
    rag_manager=None,
) -> None:
    """Register RAG tools in the tool registry.

    Args:
        registry: ToolRegistry instance.
        rag_manager: RAGManager instance (can be None — tools return errors).
    """

    async def rag_search_handler(
        query: str, source: str = "all", limit: int = 5
    ) -> ToolResult:
        """Semantic search across documents and/or conversations."""
        if rag_manager is None:
            return ToolResult.error("RAG 系统未启用，请在配置中开启 rag.enabled")

        try:
            sources_map = {
                "all": None,
                "docs": ["docs"],
                "conversations": ["conversations"],
            }
            sources = sources_map.get(source)
            if sources is None:
                return ToolResult.error(
                    f"无效的 source 参数: '{source}'，可选值: all, docs, conversations"
                )

            results = await rag_manager.search(
                query=query, sources=sources, limit=limit
            )

            if not results:
                return ToolResult.success(
                    result="未找到相关内容。",
                    metadata={"count": 0, "query": query},
                )

            formatted = []
            for r in results:
                formatted.append({
                    "content": r.content,
                    "score": round(r.score, 4),
                    "source": r.metadata.get("source_path", "conversation"),
                    "type": r.metadata.get("type", "document"),
                })

            return ToolResult.success(
                result=formatted,
                metadata={"count": len(formatted), "query": query},
            )
        except Exception as e:
            return ToolResult.error(f"RAG 检索失败: {e}")

    async def rag_upload_handler(path: str) -> ToolResult:
        """Upload a local file to the knowledge base."""
        if rag_manager is None:
            return ToolResult.error("RAG 系统未启用")

        try:
            # Basic path traversal prevention (same pattern as file_ops.py)
            file_path = Path(path).resolve()
            result = await rag_manager.upload_document(file_path)
            replaced_msg = "（已覆盖旧版本）" if result["replaced"] else ""
            return ToolResult.success(
                result=f"上传成功 {replaced_msg}：{result['filename']}，"
                       f"共 {result['chunks']} 个文本块已索引。",
                metadata=result,
            )
        except Exception as e:
            return ToolResult.error(f"文件上传失败: {e}")

    async def rag_list_handler() -> ToolResult:
        """List uploaded documents."""
        if rag_manager is None:
            return ToolResult.error("RAG 系统未启用")

        try:
            docs = await rag_manager.list_documents()
            if not docs:
                return ToolResult.success(
                    result="知识库为空，还没有上传任何文档。"
                           "使用 rag_upload 工具上传文件。"
                )
            return ToolResult.success(
                result=docs,
                metadata={"total": len(docs)},
            )
        except Exception as e:
            return ToolResult.error(f"获取文档列表失败: {e}")

    registry.register(RAG_SEARCH_TOOL, rag_search_handler)
    registry.register(RAG_UPLOAD_TOOL, rag_upload_handler)
    registry.register(RAG_LIST_TOOL, rag_list_handler)
```

- [ ] **Step 2: 更新 tools/builtin/__init__.py**

读取当前 `__init__.py` 内容后，添加 RAG 工具导出：

```python
# 在现有 import 和 __all__ 之后添加：

from lukawi.tools.builtin.rag_search import register_rag_tools  # noqa: E402

__all__ = [
    ...  # 现有导出
    "register_rag_tools",
]
```

- [ ] **Step 3: 验证工具注册**

Run: `python -c "from lukawi.tools.builtin.rag_search import RAG_SEARCH_TOOL, RAG_UPLOAD_TOOL, RAG_LIST_TOOL; print(RAG_SEARCH_TOOL.name, RAG_UPLOAD_TOOL.name, RAG_LIST_TOOL.name)"`
Expected: `rag_search rag_upload rag_list`

- [ ] **Step 4: Commit**

```bash
git add src/lukawi/tools/builtin/rag_search.py src/lukawi/tools/builtin/__init__.py
git commit -m "feat(rag): add rag_search, rag_upload, rag_list tools"
```

---

### Task 9: 配置模型扩展

**Files:**
- Modify: `src/lukawi/config/models.py`

- [ ] **Step 1: 添加 RAG 配置模型**

在 `src/lukawi/config/models.py` 末尾（`DevConfig` 类之后）添加：

```python
class DashScopeConfig(BaseModel):
    """DashScope Embedding API configuration."""
    api_key: str = ""
    model: str = "text-embedding-v3"
    dimensions: int = Field(default=1024, ge=256, le=1024)


class RAGConfig(BaseModel):
    """RAG (Retrieval-Augmented Generation) configuration."""
    enabled: bool = True
    dashscope: DashScopeConfig = Field(default_factory=DashScopeConfig)
    chroma_db_dir: str = str(Path.home() / ".lukawi" / "chroma_db")
    chunk_size: int = Field(default=500, ge=100, le=2000)
    chunk_overlap: int = Field(default=50, ge=0, le=200)
    max_retrieval: int = 10
```

修改 `AppConfig` 类，添加 `rag` 字段：

```python
class AppConfig(BaseModel):
    model: ModelConfig = Field(default_factory=ModelConfig)
    tools: ToolPolicyConfig = Field(default_factory=ToolPolicyConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    tui: TUIConfig = Field(default_factory=TUIConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    skills: SkillsConfig = Field(default_factory=SkillsConfig)
    dev: DevConfig = Field(default_factory=DevConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)  # 🆕
```

- [ ] **Step 2: 验证配置加载**

Run: `python -c "from lukawi.config.models import RAGConfig; c = RAGConfig(); print(c.enabled, c.chunk_size, c.chroma_db_dir)"`
Expected: `True 500 [含 .lukawi/chroma_db 的路径]`

- [ ] **Step 3: Commit**

```bash
git add src/lukawi/config/models.py
git commit -m "feat(rag): add DashScopeConfig and RAGConfig to config models"
```

---

### Task 10: 集成 MemoryManager

**Files:**
- Modify: `src/lukawi/memory/manager.py`
- Modify: `src/lukawi/memory/longterm.py`

- [ ] **Step 1: 修改 MemoryManager 注入 RAGManager**

修改 `src/lukawi/memory/manager.py`：

在 `__init__` 中添加 `rag_manager` 参数；修改 `recall()` 和 `save_conversation()` 使用 RAG：

```python
from lukawi.rag.manager import RAGManager  # 🆕 import

class MemoryManager:
    def __init__(
        self,
        db_path: str = ":memory:",
        session_max_messages: int = 100,
        longterm_enabled: bool = True,
        rag_manager: RAGManager | None = None,  # 🆕
    ) -> None:
        self.session = SessionMemory(max_messages=session_max_messages)
        self.longterm_enabled = longterm_enabled
        self.rag = rag_manager  # 🆕
        self.session_manager = SessionManager(db_path=db_path)
        # Keep self.longterm for backward compat if rag is None
        self.longterm = LongTermMemory(db_path=db_path) if (longterm_enabled and rag_manager is None) else None  # ✏️ 修改

    async def initialize(self) -> None:
        if self.rag:
            await self.rag.initialize()  # 🆕
        elif self.longterm:
            await self.longterm.initialize()
        await self.session_manager.initialize()

    async def close(self) -> None:
        if self.rag:
            await self.rag.close()  # 🆕
        elif self.longterm:
            await self.longterm.close()
        await self.session_manager.close()

    async def recall(
        self, query: str, user_id: str = "default", limit: int = 5
    ) -> list[Memory]:
        if self.rag:
            results = await self.rag.search(query=query, user_id=user_id, limit=limit)
            return [
                Memory(
                    id=r.chunk_id, content=r.content,
                    metadata=r.metadata,
                    user_id=user_id, agent_id="lukawi",
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
                for r in results
            ]
        if self.longterm:
            return await self.longterm.search(query=query, user_id=user_id, limit=limit)
        return []

    async def save_conversation(
        self, user_id: str = "default", agent_id: str = "lukawi",
        summary: str | None = None,
    ) -> str | None:
        if summary is None:
            messages = self.session.get_history(limit=10)
            summary = self._generate_summary(messages)
        if self.rag:
            return await self.rag.index_conversation(
                content=summary, user_id=user_id,
                metadata={"agent_id": agent_id, "type": "conversation_summary"},
            )
        if self.longterm:
            return await self.longterm.add(
                content=summary,
                metadata={"type": "conversation_summary"},
                user_id=user_id, agent_id=agent_id,
            )
        return None
```

- [ ] **Step 2: 给 longterm.py 添加 deprecated 注释**

在 `src/lukawi/memory/longterm.py` 文件头部 docstring 后添加：

```python
# NOTE: LongTermMemory is deprecated in favor of RAGManager with ChromaDB.
# It is retained as a fallback when rag.enabled=False in config.
# New code should use RAGManager via MemoryManager.rag.
```

- [ ] **Step 3: 验证现有测试仍然通过**

Run: `pytest tests/test_memory/ -v --ignore=tests/test_memory/test_longterm.py`
Expected: 所有 test_manager, test_session, test_session_manager 测试通过

- [ ] **Step 4: Commit**

```bash
git add src/lukawi/memory/manager.py src/lukawi/memory/longterm.py
git commit -m "feat(rag): integrate RAGManager into MemoryManager, deprecate LongTermMemory"
```

---

### Task 11: CLI 启动集成

**Files:**
- Modify: `src/lukawi/cli/__init__.py`

- [ ] **Step 1: 在 create_app_context 中添加 RAG 初始化**

在 `cli/__init__.py` 的 `create_app_context()` 函数末尾（`return AppContext(...)` 之前）添加：

```python
# === RAG 初始化 ===
rag_manager: RAGManager | None = None
if config.rag.enabled and config.rag.dashscope.api_key:
    from lukawi.rag.embedder import DashScopeEmbedder
    from lukawi.rag.store import VectorStore
    from lukawi.rag.manager import RAGManager

    embedder = DashScopeEmbedder(
        api_key=config.rag.dashscope.api_key,
        model=config.rag.dashscope.model,
        dimensions=config.rag.dashscope.dimensions,
    )
    store = VectorStore(persist_dir=config.rag.chroma_db_dir)
    rag_manager = RAGManager(
        embedder=embedder,
        store=store,
        chunk_size=config.rag.chunk_size,
        chunk_overlap=config.rag.chunk_overlap,
    )
    await rag_manager.initialize()
    logger.info("RAG initialized with ChromaDB at %s", config.rag.chroma_db_dir)
elif config.rag.enabled:
    logger.warning("RAG enabled but no DASHSCOPE_API_KEY set — RAG disabled")

# 注入到 MemoryManager
memory_manager = MemoryManager(
    db_path=config.memory.longterm.db_path if config.memory.longterm.enabled else ":memory:",
    session_max_messages=config.memory.session.max_messages,
    longterm_enabled=config.memory.longterm.enabled,
    rag_manager=rag_manager,  # 🆕
)

# 注册 RAG 工具
from lukawi.tools.builtin.rag_search import register_rag_tools
register_rag_tools(tool_registry, rag_manager)
```

- [ ] **Step 2: 验证启动不报错**

Run: `python -m lukawi.main --mock status`
Expected: 状态输出中包含 `RAG=enabled` 或 `RAG=disabled (no API key)`

- [ ] **Step 3: Commit**

```bash
git add src/lukawi/cli/__init__.py
git commit -m "feat(rag): initialize RAGManager in CLI bootstrap, wire into MemoryManager and tools"
```

---

### Task 12: 默认配置

**Files:**
- Modify: `src/lukawi/data/default.yaml`

- [ ] **Step 1: 添加 RAG 配置段**

在 `src/lukawi/data/default.yaml` 末尾添加：

```yaml
# ========== RAG 检索增强生成 ==========
rag:
  enabled: true

  # DashScope Embedding API（阿里云）
  dashscope:
    api_key: ${DASHSCOPE_API_KEY}
    model: text-embedding-v3
    dimensions: 1024

  # ChromaDB 向量数据库
  chroma_db_dir: ~/.lukawi/chroma_db

  # 文档分块参数
  chunk_size: 500
  chunk_overlap: 50

  # 检索参数
  max_retrieval: 10
```

- [ ] **Step 2: 验证配置解析**

Run: `python -c "from lukawi.config.settings import load_config; cfg = load_config(); print('RAG enabled:', cfg.rag.enabled)"`

- [ ] **Step 3: Commit**

```bash
git add src/lukawi/data/default.yaml
git commit -m "feat(rag): add RAG configuration defaults to bundled config YAML"
```

---

### Task 13: 对话自动索引 Hook

**Files:**
- Modify: `src/lukawi/agent/core.py`

- [ ] **Step 1: 在 ReAct 循环中添加对话索引**

在 `agent/core.py` 的 `_observe()` 方法末尾（保存消息历史之后）添加：

```python
# 在 close() 或每个 turn 结束时调用
async def _maybe_index_conversation(self) -> None:
    """Index current conversation turn into RAG if available."""
    if self.memory.rag:
        try:
            await self.memory.save_conversation()
        except Exception as e:
            logger.warning("Failed to index conversation: %s", e)
```

并在 Agent 每次完成非工具调用的回复后调用此方法。

- [ ] **Step 2: 验证 mock 模式下不报错**

Run: `python -m lukawi.main --mock status`

- [ ] **Step 3: Commit**

```bash
git add src/lukawi/agent/core.py
git commit -m "feat(rag): add conversation auto-indexing hook in ReAct loop"
```

---

### Task 14: 端到端集成验证

**Files:**
- Create: `tests/test_rag/test_integration.py`

- [ ] **Step 1: 端到端测试**

`tests/test_rag/test_integration.py`:

```python
"""End-to-end integration tests for RAG pipeline."""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from lukawi.rag.embedder import DashScopeEmbedder
from lukawi.rag.store import VectorStore
from lukawi.rag.manager import RAGManager


@pytest.mark.slow
class TestRAGIntegration:
    """Full pipeline: upload → search → verify."""

    @pytest.fixture
    def rag_manager(self, temp_dir):
        """Create RAGManager with real ChromaDB but mocked embedder."""
        with patch("dashscope.TextEmbedding.call") as mock_embed:
            # Mock embedding: return random-like fixed vectors
            def make_embedding(texts):
                import hashlib
                embeddings = []
                hash_val = 0
                for _ in texts:
                    hash_val += 1
                    vec = [hash_val / 1024.0] * 1024
                    embeddings.append({"embedding": vec, "text_index": hash_val - 1})
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.output = {"embeddings": embeddings}
                mock_resp.usage = {"total_tokens": 10 * len(texts)}
                return mock_resp
            mock_embed.side_effect = make_embedding

            embedder = DashScopeEmbedder(api_key="sk-test")
            store = VectorStore(persist_dir=str(temp_dir / "integration_test"))
            mgr = RAGManager(embedder=embedder, store=store)
            asyncio.run(mgr.initialize())
            yield mgr
            asyncio.run(mgr.close())

    def test_upload_and_search_roundtrip(self, rag_manager, sample_text_file):
        """Upload a file then search for its content."""
        # Upload
        result = asyncio.run(rag_manager.upload_document(sample_text_file))
        assert result["chunks"] >= 1

        # Search
        results = asyncio.run(
            rag_manager.search("Lukawi Agent 框架", sources=["docs"])
        )
        assert len(results) >= 1
        assert any("Lukawi Agent" in r.content for r in results)

    def test_index_and_retrieve_conversation(self, rag_manager):
        """Index a conversation and retrieve it."""
        conv_id = asyncio.run(
            rag_manager.index_conversation(
                "用户询问了 RAG 系统的工作原理", user_id="test_user",
                metadata={"topic": "RAG"},
            )
        )
        assert conv_id is not None

        results = asyncio.run(
            rag_manager.search("RAG 工作原理", user_id="test_user",
                               sources=["conversations"])
        )
        assert len(results) >= 1
        assert "RAG" in results[0].content

    def test_list_documents_shows_uploaded(self, rag_manager, sample_text_file):
        """list_documents should include uploaded file."""
        asyncio.run(rag_manager.upload_document(sample_text_file))
        docs = asyncio.run(rag_manager.list_documents())
        filenames = [d["filename"] for d in docs]
        assert "sample.txt" in filenames
```

- [ ] **Step 2: 运行集成测试**

Run: `pytest tests/test_rag/test_integration.py -v -m slow`
Expected: 3 passed

- [ ] **Step 3: 运行全部 RAG 测试**

Run: `pytest tests/test_rag/ -v`
Expected: 所有测试通过（约 60+ 个）

- [ ] **Step 4: 最终验证 — 项目整体测试**

Run: `pytest tests/ -v --ignore=tests/test_tui/ --ignore=tests/test_memory/test_longterm.py`
Expected: 全部通过

- [ ] **Step 5: 最终 Commit**

```bash
git add tests/test_rag/test_integration.py
git commit -m "test(rag): add end-to-end integration tests for upload→search→verify pipeline"
```

---

## 完成检查清单

- [ ] Task 1: 依赖与骨架
- [ ] Task 2: 异常层次
- [ ] Task 3: Embedding 客户端
- [ ] Task 4: 文档加载器
- [ ] Task 5: ChromaDB 存储
- [ ] Task 6: 检索器
- [ ] Task 7: RAGManager
- [ ] Task 8: RAG 工具
- [ ] Task 9: 配置模型
- [ ] Task 10: MemoryManager 集成
- [ ] Task 11: CLI 启动集成
- [ ] Task 12: 默认配置
- [ ] Task 13: 对话自动索引
- [ ] Task 14: 集成验证
