"""VectorStore backed by ChromaDB — stores documents and conversations."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings


@dataclass
class DocumentChunk:
    """A single chunk of a source document."""

    id: str
    content: str
    source_path: str | Path
    chunk_index: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """A single search hit returned by ChromaDB."""

    chunk_id: str
    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorStore:
    """ChromaDB-backed vector store for documents and conversations."""

    def __init__(self, persist_dir: str | Path) -> None:
        self._persist_dir = Path(persist_dir)
        self._client: chromadb.PersistentClient | None = None
        self._collection_docs: chromadb.Collection | None = None
        self._collection_conv: chromadb.Collection | None = None

    @property
    def collection_docs(self) -> chromadb.Collection | None:
        """Public read-only access to the documents collection."""
        return self._collection_docs

    @property
    def collection_conv(self) -> chromadb.Collection | None:
        """Public read-only access to the conversations collection."""
        return self._collection_conv

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """Create the persistent client and ensure both collections exist."""
        self._client = chromadb.PersistentClient(
            path=str(self._persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection_docs = self._client.get_or_create_collection("documents")
        self._collection_conv = self._client.get_or_create_collection("conversations")

    async def close(self) -> None:
        """Release the ChromaDB client and reset collection references."""
        self._collection_docs = None
        self._collection_conv = None
        self._client = None

    # ------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------

    async def add_documents(self, chunks: list[DocumentChunk]) -> list[str]:
        """Insert document chunks and return their ids."""
        if not chunks or self._collection_docs is None:
            return []

        ids = [c.id for c in chunks]
        documents = [c.content for c in chunks]
        metadatas = [
            {
                "source_path": str(c.source_path),
                "chunk_index": c.chunk_index,
                **c.metadata,
            }
            for c in chunks
        ]
        self._collection_docs.add(ids=ids, documents=documents, metadatas=metadatas)
        return ids

    async def search_documents(
        self, query_text: str, limit: int = 5
    ) -> list[SearchResult]:
        """Semantic search over the document collection."""
        if self._collection_docs is None:
            return []

        results = self._collection_docs.query(
            query_texts=[query_text], n_results=limit
        )
        return self._parse_results(results)

    async def delete_document(self, source_path: str) -> int:
        """Remove all chunks belonging to *source_path*.  Returns the count removed."""
        if self._collection_docs is None:
            return 0

        existing = self._collection_docs.get(
            where={"source_path": source_path},
            include=[],
        )
        chunk_ids: list[str] = existing["ids"]  # type: ignore[index]
        if not chunk_ids:
            return 0

        self._collection_docs.delete(ids=chunk_ids)
        return len(chunk_ids)

    # ------------------------------------------------------------------
    # Conversations
    # ------------------------------------------------------------------

    async def add_conversation(
        self, content: str, metadata: dict[str, Any] | None = None
    ) -> str:
        """Store a conversation entry and return its UUID4 id."""
        if self._collection_conv is None:
            return ""

        conv_id = str(uuid.uuid4())
        self._collection_conv.add(
            ids=[conv_id],
            documents=[content],
            metadatas=[metadata] if metadata else None,
        )
        return conv_id

    async def search_conversations(
        self,
        query_text: str,
        user_id: str,
        limit: int = 5,
    ) -> list[SearchResult]:
        """Search conversations scoped to *user_id*."""
        if self._collection_conv is None:
            return []

        results = self._collection_conv.query(
            query_texts=[query_text],
            n_results=limit,
            where={"user_id": user_id},
        )
        return self._parse_results(results)

    async def delete_conversation(self, conv_id: str) -> bool:
        """Delete a single conversation by id.  Return True if it existed."""
        if self._collection_conv is None:
            return False

        existing = self._collection_conv.get(ids=[conv_id], include=[])
        if not existing["ids"]:  # type: ignore[index]
            return False

        self._collection_conv.delete(ids=[conv_id])
        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_results(results: Any) -> list[SearchResult]:
        """Convert ChromaDB query output to a list of SearchResult."""
        out: list[SearchResult] = []
        # results dict keys: ids, documents, distances, metadatas
        # Each value is list-of-lists (one inner list per query text).
        try:
            ids = results["ids"][0]  # type: ignore[index]
            documents = results.get("documents") or [[]]
            docs = documents[0] if documents else [""] * len(ids)
            distances = results.get("distances") or [[]]
            dists = distances[0] if distances else [0.0] * len(ids)
            metadatas = results.get("metadatas") or [[]]
            metas = metadatas[0] if metadatas else [{}] * len(ids)

            for i, chunk_id in enumerate(ids):
                out.append(
                    SearchResult(
                        chunk_id=chunk_id,
                        content=docs[i] if i < len(docs) else "",
                        score=1.0 - float(dists[i]) if i < len(dists) else 0.0,
                        metadata=metas[i] if i < len(metas) else {},
                    )
                )
        except (KeyError, IndexError, TypeError):
            return []

        return out
