"""Tests for lukawi.rag.store — ChromaDB-backed VectorStore."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import pytest

from lukawi.rag.store import DocumentChunk, VectorStore


# ---------------------------------------------------------------------------
# TestVectorStoreInit
# ---------------------------------------------------------------------------

class TestVectorStoreInit:
    def test_init_creates_store(self) -> None:
        store = VectorStore(persist_dir="./data/vectors")
        assert store._persist_dir == Path("./data/vectors")

    def test_initialize_creates_collections(self, tmp_path: Path) -> None:
        store = VectorStore(persist_dir=tmp_path)
        asyncio.run(store.initialize())
        try:
            assert store._collection_docs is not None
            assert store._collection_conv is not None
            assert store._collection_docs.name == "documents"
            assert store._collection_conv.name == "conversations"
        finally:
            asyncio.run(store.close())

    def test_close_cleans_up(self, tmp_path: Path) -> None:
        store = VectorStore(persist_dir=tmp_path)
        asyncio.run(store.initialize())
        asyncio.run(store.close())
        assert store._client is None
        assert store._collection_docs is None
        assert store._collection_conv is None


# ---------------------------------------------------------------------------
# Fixtures for TestAddAndSearchDocuments
# ---------------------------------------------------------------------------

@pytest.fixture
def store(tmp_path: Path):
    """Initialised VectorStore that auto-closes after the test."""
    vs = VectorStore(persist_dir=tmp_path)
    asyncio.run(vs.initialize())
    yield vs
    asyncio.run(vs.close())


@pytest.fixture
def sample_chunks() -> list[DocumentChunk]:
    return [
        DocumentChunk(
            id="c1",
            content="Lukawi is an AI agent framework with ReAct loop.",
            source_path="/docs/overview.md",
            chunk_index=0,
        ),
        DocumentChunk(
            id="c2",
            content="The framework supports tool calling and memory.",
            source_path="/docs/overview.md",
            chunk_index=1,
        ),
    ]


class TestAddAndSearchDocuments:
    def test_add_documents_returns_ids(
        self, store: VectorStore, sample_chunks: list[DocumentChunk]
    ) -> None:
        ids = asyncio.run(store.add_documents(sample_chunks))
        assert ids == ["c1", "c2"]

    def test_delete_document_by_source(
        self, store: VectorStore, sample_chunks: list[DocumentChunk]
    ) -> None:
        asyncio.run(store.add_documents(sample_chunks))
        deleted = asyncio.run(store.delete_document("/docs/overview.md"))
        assert deleted == 2

    def test_delete_nonexistent_document_returns_zero(
        self, store: VectorStore
    ) -> None:
        deleted = asyncio.run(store.delete_document("/nonexistent/file.md"))
        assert deleted == 0


# ---------------------------------------------------------------------------
# TestConversations
# ---------------------------------------------------------------------------

class TestConversations:
    def test_add_conversation_returns_id(self, store: VectorStore) -> None:
        conv_id = asyncio.run(store.add_conversation("Hello, how can I help?"))
        assert isinstance(conv_id, str)
        assert len(conv_id) == 36  # UUID4 format
        assert conv_id.count("-") == 4

    def test_delete_conversation_true_for_existing(
        self, store: VectorStore
    ) -> None:
        conv_id = asyncio.run(store.add_conversation("Test conversation", {"user_id": "u1"}))
        assert asyncio.run(store.delete_conversation(conv_id)) is True

    def test_delete_conversation_false_for_nonexistent(
        self, store: VectorStore
    ) -> None:
        assert asyncio.run(store.delete_conversation("00000000-0000-0000-0000-000000000000")) is False
