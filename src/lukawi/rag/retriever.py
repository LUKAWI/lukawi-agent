"""Unified retriever that aggregates document and conversation search."""
from __future__ import annotations

import logging

from lukawi.rag.embedder import DashScopeEmbedder
from lukawi.rag.store import SearchResult, VectorStore

logger = logging.getLogger("lukawi.rag.retriever")


class Retriever:
    """Top-level retrieval interface combining document and conversation search."""

    def __init__(self, store: VectorStore, embedder: DashScopeEmbedder) -> None:
        self.store = store
        self.embedder = embedder

    async def retrieve(
        self,
        query: str,
        user_id: str = "default",
        sources: list[str] | None = None,
        limit_per_source: int = 5,
    ) -> list[SearchResult]:
        """Search across specified sources, merge and sort by score ascending.

        Lower scores indicate higher relevance (cosine distance).
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
