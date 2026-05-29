"""VectorStore backed by ChromaDB — stores documents and conversations."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings
from chromadb.api.types import EmbeddingFunction, Embeddings


class _DummyEmbeddingFunction(EmbeddingFunction):
    """No-op embedding function that satisfies ChromaDB dimension validation.

    Used when an external embedder (DashScope / Mock) is injected into
    VectorStore.  ChromaDB never calls this because we always pass
    embeddings explicitly via ``col.add(embeddings=...)`` and
    ``col.query(query_embeddings=...)``.
    """

    def __init__(self, dimensions: int) -> None:
        self._dimensions = dimensions

    def __call__(self, texts: list[str]) -> Embeddings:
        return [[0.0] * self._dimensions for _ in texts]

    @staticmethod
    def name() -> str:
        return "lukawi-external"


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
    """ChromaDB-backed vector store for documents and conversations.

    When *embedder* is provided, all add and search operations use it
    to generate embeddings explicitly, bypassing ChromaDB's built-in
    ONNX embedder.  Without it, ChromaDB's default embedding is used.
    """

    def __init__(self, persist_dir: str | Path, embedder=None) -> None:
        self._persist_dir = Path(persist_dir)
        self._embedder = embedder
        self._client: chromadb.PersistentClient | None = None
        self._collection_docs: chromadb.Collection | None = None
        self._collection_conv: chromadb.Collection | None = None
        self._initialized: bool = False

    @property
    def collection_docs(self) -> chromadb.Collection | None:
        """Public read-only access to the documents collection."""
        return self._collection_docs

    @property
    def collection_conv(self) -> chromadb.Collection | None:
        """Public read-only access to the conversations collection."""
        return self._collection_conv

    # ------------------------------------------------------------------
    # Helpers — run sync ChromaDB calls off the event loop
    # ------------------------------------------------------------------

    @staticmethod
    async def _run_sync(call, *args, **kwargs):
        """Run a synchronous ChromaDB call in a thread to avoid blocking the event loop.

        ChromaDB exceptions are caught and re-raised as StorageError with context.
        """
        try:
            return await asyncio.to_thread(call, *args, **kwargs)
        except Exception as e:
            from lukawi.rag.exceptions import RAGError

            if not isinstance(e, RAGError):
                raise RuntimeError(f"ChromaDB operation failed: {e}") from e
            raise

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """Create the persistent client and ensure both collections exist."""
        if self._initialized:
            return

        embedding_function = None
        if self._embedder:
            emb_test = await self._embedder.embed("init")
            dims = len(emb_test[0].embedding)
            embedding_function = _DummyEmbeddingFunction(dimensions=dims)

        ef = embedding_function

        def _init() -> None:
            client = chromadb.PersistentClient(
                path=str(self._persist_dir),
                settings=Settings(anonymized_telemetry=False),
            )
            self._client = client

            for name in ("documents", "conversations"):
                col = self._get_or_init_collection(client, name, ef)
                if name == "documents":
                    self._collection_docs = col
                else:
                    self._collection_conv = col

        await self._run_sync(_init)
        self._initialized = True

    @staticmethod
    def _get_or_init_collection(client, name, embedding_function=None):
        """Get or create a ChromaDB collection, handling external embedder migration."""
        if embedding_function is None:
            return client.get_or_create_collection(name)

        try:
            return client.get_collection(name, embedding_function=embedding_function)
        except Exception:
            pass

        try:
            return client.create_collection(name, embedding_function=embedding_function)
        except Exception:
            client.delete_collection(name)
            return client.create_collection(name, embedding_function=embedding_function)

    async def close(self) -> None:
        """Release the ChromaDB client and reset collection references."""
        self._collection_docs = None
        self._collection_conv = None
        self._client = None
        self._initialized = False

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
        col = self._collection_docs

        if self._embedder:
            emb_results = await self._embedder.embed(documents)
            embeddings = [r.embedding for r in emb_results]

            def _add():
                col.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

            await self._run_sync(_add)
        else:

            def _add():
                col.add(ids=ids, documents=documents, metadatas=metadatas)

            await self._run_sync(_add)
        return ids

    async def search_documents(
        self, query_text: str, limit: int = 5, source_path: str | None = None, source_paths: list[str] | None = None
    ) -> list[SearchResult]:
        """Semantic search over the document collection, optionally scoped to *source_paths*."""
        if self._collection_docs is None:
            return []

        col = self._collection_docs

        all_paths = list(source_paths or [])
        if source_path and source_path not in all_paths:
            all_paths.append(source_path)

        if self._embedder:
            emb_results = await self._embedder.embed(query_text)
            query_embeddings = [emb_results[0].embedding]

            def _query():
                kwargs: dict = {"query_embeddings": query_embeddings, "n_results": limit}
                where = _build_where(all_paths)
                if where:
                    kwargs["where"] = where
                return col.query(**kwargs)
        else:

            def _query():
                kwargs: dict = {"query_texts": [query_text], "n_results": limit}
                where = _build_where(all_paths)
                if where:
                    kwargs["where"] = where
                return col.query(**kwargs)

        results = await self._run_sync(_query)
        return self._parse_results(results)

    async def delete_document(self, source_path: str) -> int:
        """Remove all chunks belonging to *source_path*.  Returns the count removed."""
        if self._collection_docs is None:
            return 0

        col = self._collection_docs

        def _delete():
            existing = col.get(where={"source_path": source_path}, include=[])
            chunk_ids: list[str] = existing["ids"]
            if not chunk_ids:
                return 0
            col.delete(ids=chunk_ids)
            return len(chunk_ids)

        return await self._run_sync(_delete)

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
        col = self._collection_conv

        if self._embedder:
            emb_results = await self._embedder.embed(content)
            embedding = emb_results[0].embedding

            def _add():
                col.add(
                    ids=[conv_id],
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[metadata] if metadata else None,
                )

            await self._run_sync(_add)
        else:

            def _add():
                col.add(
                    ids=[conv_id],
                    documents=[content],
                    metadatas=[metadata] if metadata else None,
                )

            await self._run_sync(_add)
        return conv_id

    async def search_conversations(
        self,
        query_text: str,
        user_id: str,
        limit: int = 5,
        session_id: str | None = None,
    ) -> list[SearchResult]:
        """Search conversations scoped to *user_id* and optionally *session_id*."""
        if self._collection_conv is None:
            return []

        col = self._collection_conv

        if session_id:
            where: dict = {"$and": [{"user_id": user_id}, {"session_id": session_id}]}
        else:
            where: dict = {"user_id": user_id}

        if self._embedder:
            emb_results = await self._embedder.embed(query_text)
            query_embeddings = [emb_results[0].embedding]

            def _query():
                return col.query(
                    query_embeddings=query_embeddings,
                    n_results=limit,
                    where=where,
                )
        else:

            def _query():
                return col.query(
                    query_texts=[query_text],
                    n_results=limit,
                    where=where,
                )

        results = await self._run_sync(_query)
        return self._parse_results(results)

    async def delete_conversation(self, conv_id: str) -> bool:
        """Delete a single conversation by id.  Return True if it existed."""
        if self._collection_conv is None:
            return False

        col = self._collection_conv

        def _delete():
            existing = col.get(ids=[conv_id], include=[])
            if not existing["ids"]:
                return False
            col.delete(ids=[conv_id])
            return True

        return await self._run_sync(_delete)

    async def clear_conversations(self) -> int:
        """Delete ALL conversation entries.  Returns the count removed."""
        if self._collection_conv is None:
            return 0

        col = self._collection_conv

        def _clear():
            existing = col.get(include=[])
            all_ids = existing["ids"]
            if not all_ids:
                return 0
            col.delete(ids=all_ids)
            return len(all_ids)

        return await self._run_sync(_clear)

    async def clear_conversations_by_session(self, session_id: str) -> int:
        """Delete conversation entries scoped to *session_id*. Returns count removed."""
        if self._collection_conv is None:
            return 0

        col = self._collection_conv

        def _clear():
            existing = col.get(where={"session_id": session_id}, include=[])
            chunk_ids = existing["ids"]
            if not chunk_ids:
                return 0
            col.delete(ids=chunk_ids)
            return len(chunk_ids)

        return await self._run_sync(_clear)

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


def _build_where(source_paths: list[str]) -> dict | None:
    if not source_paths:
        return None
    if len(source_paths) == 1:
        return {"source_path": source_paths[0]}
    return {"$or": [{"source_path": p} for p in source_paths]}
