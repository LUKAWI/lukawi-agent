"""RAG lifecycle manager — orchestrate embedding, storage, and retrieval."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

from lukawi.rag.embedder import DashScopeEmbedder
from lukawi.rag.store import VectorStore, SearchResult
from lukawi.rag.document import DocumentLoader
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
        """Initialize store and create retriever."""
        if self.retriever is not None:
            return
        await self.store.initialize()
        self.retriever = Retriever(store=self.store)
        logger.info("RAGManager initialized")

    async def close(self) -> None:
        """Close store resources."""
        await self.store.close()
        self.retriever = None
        logger.info("RAGManager closed")

    async def upload_document(self, path: str | Path, display_name: str | None = None) -> dict:
        """Upload a document: validate, load, chunk, and store. Replaces existing if same path."""
        path = Path(path)
        source_key = display_name or str(path)
        self._validate_file(path)
        existing = await self.store.delete_document(source_key)
        loader = DocumentLoader(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        chunks = loader.load_file(path, source_path=source_key)
        await self.store.add_documents(chunks)
        return {"path": source_key, "filename": Path(source_key).name, "chunks": len(chunks), "replaced": existing > 0}

    async def search(self, query: str, user_id: str = "default", sources: list[str] | None = None, limit: int = 5, session_id: str | None = None, source_path: str | None = None) -> list[SearchResult]:
        """Unified search across documents and conversations."""
        if not self.retriever:
            raise DocumentLoadError("RAGManager not initialized")
        return await self.retriever.retrieve(query=query, user_id=user_id, sources=sources, limit_per_source=limit, session_id=session_id, source_path=source_path)

    async def index_conversation(self, content: str, user_id: str = "default", metadata: dict | None = None, session_id: str | None = None) -> str:
        """Index a conversation summary into ChromaDB."""
        meta = metadata or {}
        meta.setdefault("user_id", user_id)
        meta.setdefault("type", "conversation_summary")
        meta.setdefault("created_at", datetime.now(UTC).isoformat())
        if session_id:
            meta["session_id"] = session_id
        return await self.store.add_conversation(content=content, metadata=meta)

    async def list_documents(self) -> list[dict]:
        """List all uploaded documents grouped by source path."""
        col = self.store.collection_docs
        if not col:
            return []

        def _list():
            return col.get(include=["metadatas"])

        results = await self.store._run_sync(_list)
        if not results or not results.get("ids"):
            return []
        seen: dict[str, dict] = {}
        for meta in results.get("metadatas", []):
            source = meta.get("source_path", "unknown")
            if source not in seen:
                seen[source] = {"path": source, "filename": Path(source).name, "chunks": 1}
            else:
                seen[source]["chunks"] += 1
        return list(seen.values())

    async def remove_document(self, source_path: str) -> int:
        """Remove all chunks of a document by source path."""
        return await self.store.delete_document(source_path)

    def _validate_file(self, path: Path) -> None:
        """Validate file exists, is supported format, and within size limit."""
        if not path.exists():
            raise DocumentLoadError(f"文件不存在: {path}")
        if not path.is_file():
            raise DocumentLoadError(f"不是文件: {path}")
        if path.suffix.lower() not in (".txt", ".md", ".markdown"):
            raise DocumentLoadError(f"不支持的文件格式: {path.suffix}，当前支持 .txt / .md")
        if path.stat().st_size > MAX_FILE_SIZE:
            raise DocumentLoadError("文件过大，请限制在 10MB 以内")
