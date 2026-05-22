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
