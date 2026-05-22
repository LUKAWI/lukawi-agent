"""RAG module — Retrieval-Augmented Generation with DashScope embeddings and ChromaDB."""

from __future__ import annotations

from lukawi.rag.exceptions import (
    DocumentLoadError,
    EmbeddingError,
    RAGError,
    StorageError,
)
from lukawi.rag.retriever import Retriever  # noqa: E402
from lukawi.rag.store import DocumentChunk, SearchResult, VectorStore

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
