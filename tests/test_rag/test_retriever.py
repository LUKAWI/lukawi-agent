"""Tests for Retriever."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, AsyncMock

from lukawi.rag.retriever import Retriever
from lukawi.rag.store import SearchResult


class TestRetriever:
    """Tests for the unified Retriever class."""

    @pytest.fixture
    def mock_store(self):
        """A VectorStore with mocked search methods."""
        store = MagicMock()
        store.search_documents = AsyncMock()
        store.search_conversations = AsyncMock()
        return store

    @pytest.fixture
    def mock_embedder(self):
        """A DashScopeEmbedder mock."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_retrieve_documents_delegates(self, mock_store, mock_embedder):
        """retrieve_documents should delegate to store.search_documents."""
        expected = [SearchResult(chunk_id="c1", content="hello", score=0.5)]
        mock_store.search_documents.return_value = expected

        retriever = Retriever(store=mock_store, embedder=mock_embedder)
        result = await retriever.retrieve_documents("hello", limit=3)

        mock_store.search_documents.assert_called_once_with(
            query_text="hello", limit=3
        )
        assert result[0].chunk_id == "c1"

    @pytest.mark.asyncio
    async def test_retrieve_conversations_delegates(self, mock_store, mock_embedder):
        """retrieve_conversations should delegate to store.search_conversations."""
        expected = [SearchResult(chunk_id="cv1", content="hi there", score=0.4)]
        mock_store.search_conversations.return_value = expected

        retriever = Retriever(store=mock_store, embedder=mock_embedder)
        result = await retriever.retrieve_conversations(
            "hello", user_id="u1", limit=3
        )

        mock_store.search_conversations.assert_called_once_with(
            query_text="hello", user_id="u1", limit=3
        )
        assert result[0].chunk_id == "cv1"

    @pytest.mark.asyncio
    async def test_retrieve_all_merges_and_sorts(self, mock_store, mock_embedder):
        """retrieve() should merge results from all sources and sort by score DESC."""
        mock_store.search_documents.return_value = [
            SearchResult(chunk_id="d1", content="doc a", score=0.7),
            SearchResult(chunk_id="d2", content="doc b", score=0.3),
        ]
        mock_store.search_conversations.return_value = [
            SearchResult(chunk_id="cv1", content="conv a", score=0.9),
        ]

        retriever = Retriever(store=mock_store, embedder=mock_embedder)
        results = await retriever.retrieve("query")

        scores = [r.score for r in results]
        # Higher score = better (score = 1 - cosine distance), sorted descending
        assert scores == [0.9, 0.7, 0.3]

    @pytest.mark.asyncio
    async def test_retrieve_source_filter(self, mock_store, mock_embedder):
        """retrieve() with sources=['docs'] should NOT call search_conversations."""
        mock_store.search_documents.return_value = [
            SearchResult(chunk_id="d1", content="doc", score=0.5),
        ]

        retriever = Retriever(store=mock_store, embedder=mock_embedder)
        await retriever.retrieve("query", sources=["docs"])

        mock_store.search_documents.assert_called_once()
        mock_store.search_conversations.assert_not_called()

    @pytest.mark.asyncio
    async def test_retrieve_sort_order_regression(self, mock_store, mock_embedder):
        """retrieve() must always return results sorted by score DESC (highest first).

        Regression: score=1.0-distance, so higher score = more relevant.
        """
        mock_store.search_documents.return_value = [
            SearchResult(chunk_id="d1", content="low", score=0.2),
            SearchResult(chunk_id="d2", content="high", score=0.9),
        ]
        mock_store.search_conversations.return_value = [
            SearchResult(chunk_id="cv1", content="mid", score=0.5),
        ]

        retriever = Retriever(store=mock_store, embedder=mock_embedder)
        results = await retriever.retrieve("query")

        assert results[0].score >= results[-1].score, "Must be sorted DESC"
        assert results[0].chunk_id == "d2", "Highest score should be first"
