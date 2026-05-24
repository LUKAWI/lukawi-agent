"""Unified retriever that aggregates document and conversation search."""
from __future__ import annotations

import logging

from lukawi.rag.store import SearchResult, VectorStore

logger = logging.getLogger("lukawi.rag.retriever")


class Retriever:
    """Top-level retrieval interface combining document and conversation search."""

    def __init__(self, store: VectorStore) -> None:
        self.store = store

    async def retrieve(
        self,
        query: str,
        user_id: str = "default",
        sources: list[str] | None = None,
        limit_per_source: int = 5,
        session_id: str | None = None,
        source_path: str | None = None,
    ) -> list[SearchResult]:
        """Search across specified sources, merge and sort by score descending.

        Higher scores indicate higher relevance (score = 1 - cosine distance).
        """
        if sources is None:
            sources = ["docs", "conversations"]

        all_results: list[SearchResult] = []

        if "docs" in sources:
            doc_results = await self.retrieve_documents(query, limit=limit_per_source, source_path=source_path)
            all_results.extend(doc_results)

        if "conversations" in sources:
            conv_results = await self.retrieve_conversations(
                query, user_id=user_id, limit=limit_per_source, session_id=session_id
            )
            all_results.extend(conv_results)

        all_results.sort(key=lambda r: r.score, reverse=True)
        return all_results

    async def retrieve_documents(
        self, query: str, limit: int = 5, source_path: str | None = None
    ) -> list[SearchResult]:
        """Search only the documents collection, optionally scoped to *source_path*."""
        return await self.store.search_documents(query_text=query, limit=limit, source_path=source_path)

    async def retrieve_conversations(
        self, query: str, user_id: str = "default", limit: int = 5, session_id: str | None = None
    ) -> list[SearchResult]:
        """Search only the conversations collection."""
        return await self.store.search_conversations(
            query_text=query, user_id=user_id, limit=limit, session_id=session_id
        )
