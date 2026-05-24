"""Embedding clients — DashScope text-embedding-v3 and MockEmbedder for development."""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field

from lukawi.rag.exceptions import EmbeddingError

logger = logging.getLogger("lukawi.rag.embedder")


@dataclass
class EmbeddingResult:
    """Single embedding API result."""

    embedding: list[float]
    model: str
    tokens_used: int = 0
    metadata: dict = field(default_factory=dict)


class DashScopeEmbedder:
    """Client for DashScope text-embedding-v3 API."""

    MAX_BATCH_SIZE = 10

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-v3",
        dimensions: int = 1024,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.dimensions = dimensions

    async def embed(self, texts: str | list[str]) -> list[EmbeddingResult]:
        """Embed one or more texts. Auto-batches if >25 texts."""
        if isinstance(texts, str):
            return [await self.embed_single(texts)]
        results: list[EmbeddingResult] = []
        for i in range(0, len(texts), self.MAX_BATCH_SIZE):
            batch = texts[i : i + self.MAX_BATCH_SIZE]
            batch_results = await self._embed_batch(batch)
            results.extend(batch_results)
        return results

    async def embed_single(self, text: str) -> EmbeddingResult:
        """Embed a single text string."""
        results = await self._embed_batch([text])
        return results[0]

    async def _embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Call DashScope API with retry logic."""
        import dashscope
        from http import HTTPStatus

        max_retries = 3
        last_error = None
        for attempt in range(max_retries):
            try:
                resp = dashscope.TextEmbedding.call(
                    model=self.model,
                    input=texts,
                    dimension=self.dimensions,
                    api_key=self.api_key,
                )
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait = 2**attempt
                    logger.warning(
                        "Embedding API error, retrying in %ds (attempt %d/%d): %s",
                        wait,
                        attempt + 1,
                        max_retries,
                        e,
                    )
                    await asyncio.sleep(wait)
                    continue
                raise EmbeddingError(
                    f"Embedding API failed after {max_retries} attempts", cause=e
                ) from e

            if resp.status_code == HTTPStatus.OK:
                return [
                    EmbeddingResult(
                        embedding=item["embedding"],
                        model=self.model,
                        tokens_used=resp.usage.get("total_tokens", 0)
                        if resp.usage
                        else 0,
                        metadata={"index": i},
                    )
                    for i, item in enumerate(resp.output["embeddings"])
                ]
            elif resp.status_code == 429:
                last_error = Exception(f"Rate limit: {resp.message}")
                if attempt < max_retries - 1:
                    wait = 2**attempt
                    logger.warning("Rate limited, retrying in %ds", wait)
                    await asyncio.sleep(wait)
                    continue
                raise EmbeddingError(f"Rate limit exceeded: {resp.message}")
            elif resp.status_code in (401, 403):
                raise EmbeddingError(f"Authentication failed: {resp.message}")
            else:
                last_error = Exception(
                    f"API error {resp.status_code}: {resp.message}"
                )
                if attempt < max_retries - 1:
                    wait = 2**attempt
                    await asyncio.sleep(wait)
                    continue
                raise EmbeddingError(
                    f"Unexpected API error ({resp.status_code}): {resp.message}"
                )

        raise EmbeddingError("All retries exhausted", cause=last_error)


class MockEmbedder:
    """Deterministic mock embedder for development without API key.

    Generates hash-based embeddings at 1024 dimensions (matching DashScope's
    text-embedding-v3 default) so ChromaDB can perform distance computations
    with realistic dimensionality.
    """

    DIMENSIONS = 1024

    def __init__(self, dimensions: int | None = None) -> None:
        self.model = "mock-embedder"
        self.dimensions = dimensions or self.DIMENSIONS

    async def embed(self, texts: str | list[str]) -> list[EmbeddingResult]:
        if isinstance(texts, str):
            return [self._embed_single(texts)]
        return [self._embed_single(t) for t in texts]

    async def embed_single(self, text: str) -> EmbeddingResult:
        return self._embed_single(text)

    def _embed_single(self, text: str) -> EmbeddingResult:
        vec = self._hash_to_vector(text)
        return EmbeddingResult(
            embedding=vec,
            model=self.model,
            tokens_used=len(text) // 4,
            metadata={},
        )

    def _hash_to_vector(self, text: str) -> list[float]:
        """Generate a deterministic unit vector from text content."""
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()
        vec = [int(h[i : i + 2], 16) / 255.0 for i in range(0, min(len(h), self.dimensions * 2), 2)]
        while len(vec) < self.dimensions:
            vec.append(0.0)
        vec = vec[: self.dimensions]
        norm = sum(x * x for x in vec) ** 0.5
        if norm < 1e-10:
            return [0.0] * self.dimensions
        return [x / norm for x in vec]
