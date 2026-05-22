"""Tests for RAGManager."""
from __future__ import annotations

import asyncio

import pytest
from unittest.mock import AsyncMock, MagicMock

from lukawi.rag.manager import RAGManager
from lukawi.rag.exceptions import DocumentLoadError


class TestRAGManagerLifecycle:
    def test_init_stores_dependencies(self, mock_embedder, mock_store):
        """RAGManager should store embedder and store."""
        mgr = RAGManager(embedder=mock_embedder, store=mock_store)
        assert mgr.embedder is mock_embedder
        assert mgr.store is mock_store

    def test_initialize_delegates_to_store(self, mock_embedder, mock_store):
        """initialize() should call store.initialize()."""
        mgr = RAGManager(embedder=mock_embedder, store=mock_store)
        asyncio.run(mgr.initialize())
        mock_store.initialize.assert_awaited_once()


class TestUploadDocument:
    def test_upload_rejects_unsupported_format(self, mock_embedder, mock_store, temp_dir):
        """Non-txt/md files should be rejected."""
        path = temp_dir / "image.png"
        path.write_bytes(b"\x89PNG\x0d\x0a")
        mgr = RAGManager(embedder=mock_embedder, store=mock_store)
        with pytest.raises(DocumentLoadError, match="不支持"):
            asyncio.run(mgr.upload_document(path))

    def test_upload_success_returns_chunk_count(self, mock_embedder, mock_store, sample_text_file):
        """Upload should return chunk count and file info."""
        mock_store.delete_document = AsyncMock(return_value=0)
        mock_store.add_documents = AsyncMock(return_value=["c1"])
        mgr = RAGManager(embedder=mock_embedder, store=mock_store)
        result = asyncio.run(mgr.upload_document(sample_text_file))
        assert result["chunks"] >= 1
        assert result["filename"] == "sample.txt"

    def test_upload_replaces_existing(self, mock_embedder, mock_store, sample_text_file):
        """Re-upload should mark replaced=True."""
        mock_store.delete_document = AsyncMock(return_value=2)
        mock_store.add_documents = AsyncMock(return_value=["c1", "c2"])
        mgr = RAGManager(embedder=mock_embedder, store=mock_store)
        result = asyncio.run(mgr.upload_document(sample_text_file))
        assert result["replaced"] is True


class TestListDocuments:
    def test_list_documents_empty(self, mock_embedder, mock_store):
        """list_documents with no documents should return empty list."""
        mock_store.collection_docs = MagicMock()
        mock_store.collection_docs.get.return_value = {"ids": [], "metadatas": []}
        mgr = RAGManager(embedder=mock_embedder, store=mock_store)
        docs = asyncio.run(mgr.list_documents())
        assert docs == []

    def test_list_documents_returns_grouped(self, mock_embedder, mock_store):
        """list_documents should group chunks by source_path."""
        mock_store.collection_docs = MagicMock()
        mock_store.collection_docs.get.return_value = {
            "ids": ["c1", "c2"],
            "metadatas": [
                {"source_path": "/tmp/doc1.txt"},
                {"source_path": "/tmp/doc1.txt"},
            ],
        }
        mgr = RAGManager(embedder=mock_embedder, store=mock_store)
        docs = asyncio.run(mgr.list_documents())
        assert len(docs) == 1
        assert docs[0]["filename"] == "doc1.txt"
        assert docs[0]["chunks"] == 2


class TestSearch:
    def test_search_requires_initialization(self, mock_embedder, mock_store):
        """search() should raise if retriever is None (not initialized)."""
        mgr = RAGManager(embedder=mock_embedder, store=mock_store)
        with pytest.raises(DocumentLoadError, match="not initialized"):
            asyncio.run(mgr.search("test query"))

    def test_search_delegates_to_retriever(self, mock_embedder, mock_store):
        """search() should call retriever.retrieve()."""
        mock_store.initialize = AsyncMock()
        mock_retriever = MagicMock()
        mock_retriever.retrieve = AsyncMock(return_value=[])
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("lukawi.rag.manager.Retriever", lambda **kw: mock_retriever)
            mgr = RAGManager(embedder=mock_embedder, store=mock_store)
            asyncio.run(mgr.initialize())
            asyncio.run(mgr.search("hello", user_id="u1", limit=3))
        mock_retriever.retrieve.assert_awaited_once_with(
            query="hello", user_id="u1", sources=None, limit_per_source=3
        )


class TestIndexConversation:
    def test_index_conversation_delegates_to_store(self, mock_embedder, mock_store):
        """index_conversation() should call store.add_conversation()."""
        mock_store.add_conversation = AsyncMock(return_value="abc123")
        mgr = RAGManager(embedder=mock_embedder, store=mock_store)
        conv_id = asyncio.run(mgr.index_conversation("summary text", user_id="u2"))
        assert conv_id == "abc123"
        mock_store.add_conversation.assert_awaited_once()
        call_kwargs = mock_store.add_conversation.call_args.kwargs
        assert call_kwargs["content"] == "summary text"
        assert call_kwargs["metadata"]["user_id"] == "u2"
        assert call_kwargs["metadata"]["type"] == "conversation_summary"


class TestRemoveDocument:
    def test_remove_document_delegates_to_store(self, mock_embedder, mock_store):
        """remove_document() should call store.delete_document()."""
        mock_store.delete_document = AsyncMock(return_value=5)
        mgr = RAGManager(embedder=mock_embedder, store=mock_store)
        count = asyncio.run(mgr.remove_document("/tmp/removed.txt"))
        assert count == 5
        mock_store.delete_document.assert_awaited_once_with("/tmp/removed.txt")
