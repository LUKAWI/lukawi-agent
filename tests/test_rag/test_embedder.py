"""Tests for DashScopeEmbedder."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from lukawi.rag.embedder import DashScopeEmbedder, EmbeddingResult


# ---------------------------------------------------------------------------
# shared helpers
# ---------------------------------------------------------------------------

def _mock_response(embeddings=None, tokens=5, status_code=200):
    """Build a MagicMock that looks like a DashScope embedding response."""
    if embeddings is None:
        embeddings = [{"embedding": [0.1] * 1024, "text_index": 0}]
    resp = MagicMock()
    resp.status_code = status_code
    resp.output = {"embeddings": embeddings}
    resp.usage = {"total_tokens": tokens}
    resp.message = ""
    return resp


def _embed_call_kwargs(mock_call):
    """Return the keyword arguments passed to dashscope.TextEmbedding.call."""
    return mock_call.call_args.kwargs


# ---------------------------------------------------------------------------
# TestDashScopeEmbedderInit
# ---------------------------------------------------------------------------

class TestDashScopeEmbedderInit:
    """Unit tests for DashScopeEmbedder.__init__."""

    def test_init_with_defaults(self):
        embedder = DashScopeEmbedder(api_key="sk-test")
        assert embedder.model == "text-embedding-v3"
        assert embedder.dimensions == 1024
        assert embedder.api_key == "sk-test"

    def test_init_with_custom_model(self):
        embedder = DashScopeEmbedder(api_key="sk-test", model="text-embedding-v2")
        assert embedder.model == "text-embedding-v2"
        assert embedder.dimensions == 1024

    def test_init_with_custom_dimensions(self):
        embedder = DashScopeEmbedder(api_key="sk-test", dimensions=768)
        assert embedder.dimensions == 768
        assert embedder.model == "text-embedding-v3"


# ---------------------------------------------------------------------------
# TestDashScopeEmbedSingle
# ---------------------------------------------------------------------------

class TestDashScopeEmbedSingle:
    """Tests for embed_single."""

    def test_embed_single_returns_embedding_result(self):
        embedder = DashScopeEmbedder(api_key="sk-test")
        mock_resp = _mock_response()

        with patch("dashscope.TextEmbedding.call", return_value=mock_resp):
            result = asyncio.run(embedder.embed_single("hello"))

        assert isinstance(result, EmbeddingResult)
        assert len(result.embedding) == 1024
        assert result.model == "text-embedding-v3"
        assert result.tokens_used == 5

    def test_embed_single_tokens_usage(self):
        embedder = DashScopeEmbedder(api_key="sk-test")
        mock_resp = _mock_response(tokens=8)

        with patch("dashscope.TextEmbedding.call", return_value=mock_resp):
            result = asyncio.run(embedder.embed_single("hello"))

        assert result.tokens_used == 8

    def test_embed_with_custom_dimensions(self):
        embedder = DashScopeEmbedder(api_key="sk-test", dimensions=768)
        emb = [0.1] * 768
        mock_resp = _mock_response(
            embeddings=[{"embedding": emb, "text_index": 0}], tokens=5
        )

        with patch("dashscope.TextEmbedding.call", return_value=mock_resp) as mock_call:
            result = asyncio.run(embedder.embed_single("hello"))

        assert len(result.embedding) == 768
        assert _embed_call_kwargs(mock_call)["dimension"] == 768


# ---------------------------------------------------------------------------
# TestDashScopeEmbedBatch
# ---------------------------------------------------------------------------

class TestDashScopeEmbedBatch:
    """Tests for the embed method (batch / single dispatch)."""

    def test_embed_list_returns_multiple_results(self):
        embedder = DashScopeEmbedder(api_key="sk-test")
        emb_a = [round(i * 0.1, 12) for i in range(1024)]
        emb_b = [round(i * 0.2, 12) for i in range(1024)]
        emb_c = [round(i * 0.3, 12) for i in range(1024)]
        mock_resp = _mock_response(
            embeddings=[
                {"embedding": emb_a, "text_index": 0},
                {"embedding": emb_b, "text_index": 1},
                {"embedding": emb_c, "text_index": 2},
            ],
            tokens=15,
        )

        with patch("dashscope.TextEmbedding.call", return_value=mock_resp):
            results = asyncio.run(embedder.embed(["a", "b", "c"]))

        assert len(results) == 3
        assert results[0].embedding == emb_a
        assert results[1].embedding == emb_b
        assert results[2].embedding == emb_c
        assert all(isinstance(r, EmbeddingResult) for r in results)
        assert results[0].tokens_used == 15

    def test_embed_str_returns_single_result_list(self):
        embedder = DashScopeEmbedder(api_key="sk-test")
        mock_resp = _mock_response()

        with patch("dashscope.TextEmbedding.call", return_value=mock_resp):
            results = asyncio.run(embedder.embed("single"))

        assert len(results) == 1
        assert isinstance(results[0], EmbeddingResult)
        assert results[0].model == "text-embedding-v3"


# ---------------------------------------------------------------------------
# TestMockEmbedder
# ---------------------------------------------------------------------------

class TestMockEmbedder:
    """Tests for MockEmbedder — deterministic hash-based embedder."""

    def test_default_dimensions_match_dashscope(self):
        from lukawi.rag.embedder import MockEmbedder
        embedder = MockEmbedder()
        assert embedder.dimensions == 1024
        assert embedder.model == "mock-embedder"
        assert embedder.DIMENSIONS == 1024

    def test_custom_dimensions(self):
        from lukawi.rag.embedder import MockEmbedder
        embedder = MockEmbedder(dimensions=128)
        assert embedder.dimensions == 128

    def test_embed_single_returns_embedding_result(self):
        from lukawi.rag.embedder import MockEmbedder
        embedder = MockEmbedder()
        result = asyncio.run(embedder.embed_single("hello world"))
        assert isinstance(result, EmbeddingResult)
        assert len(result.embedding) == 1024
        assert result.model == "mock-embedder"

    def test_embed_list_returns_multiple(self):
        from lukawi.rag.embedder import MockEmbedder
        embedder = MockEmbedder()
        results = asyncio.run(embedder.embed(["a", "b", "c"]))
        assert len(results) == 3
        assert all(len(r.embedding) == 1024 for r in results)

    def test_deterministic_output(self):
        from lukawi.rag.embedder import MockEmbedder
        embedder = MockEmbedder()
        r1 = asyncio.run(embedder.embed_single("same text"))
        r2 = asyncio.run(embedder.embed_single("same text"))
        assert r1.embedding == r2.embedding

    def test_different_text_different_vector(self):
        from lukawi.rag.embedder import MockEmbedder
        embedder = MockEmbedder()
        r1 = asyncio.run(embedder.embed_single("hello"))
        r2 = asyncio.run(embedder.embed_single("world"))
        assert r1.embedding != r2.embedding

    def test_unit_vector_norm(self):
        from lukawi.rag.embedder import MockEmbedder
        embedder = MockEmbedder()
        result = asyncio.run(embedder.embed_single("test vector"))
        norm = sum(x * x for x in result.embedding) ** 0.5
        assert abs(norm - 1.0) < 1e-5

    def test_empty_text_returns_unit_vector(self):
        from lukawi.rag.embedder import MockEmbedder
        embedder = MockEmbedder()
        result = asyncio.run(embedder.embed_single(""))
        norm = sum(x * x for x in result.embedding) ** 0.5
        assert abs(norm - 1.0) < 1e-5
