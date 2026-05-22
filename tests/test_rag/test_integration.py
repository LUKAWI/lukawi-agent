"""End-to-end integration tests for RAG pipeline."""
from __future__ import annotations

import asyncio
import hashlib
from unittest.mock import MagicMock, patch

import pytest

from lukawi.rag.embedder import DashScopeEmbedder
from lukawi.rag.store import VectorStore
from lukawi.rag.manager import RAGManager


@pytest.mark.slow
class TestRAGIntegration:
    @pytest.fixture
    def rag_manager(self, temp_dir):
        with patch("dashscope.TextEmbedding.call") as mock_embed:
            def make_embedding(texts):
                hash_val = 0
                embeddings = []
                for text in texts:
                    hash_val += 1
                    vec = [hash_val / 1024.0] * 1024
                    embeddings.append({"embedding": vec, "text_index": hash_val - 1})
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.output = {"embeddings": embeddings}
                mock_resp.usage = {"total_tokens": 10 * len(texts)}
                return mock_resp

            mock_embed.side_effect = make_embedding
            embedder = DashScopeEmbedder(api_key="sk-test")
            store = VectorStore(persist_dir=str(temp_dir / "integration_test"))
            mgr = RAGManager(embedder=embedder, store=store)
            asyncio.run(mgr.initialize())
            yield mgr
            asyncio.run(mgr.close())

    def test_upload_and_search_roundtrip(self, rag_manager, sample_text_file):
        result = asyncio.run(rag_manager.upload_document(sample_text_file))
        assert result["chunks"] >= 1
        results = asyncio.run(
            rag_manager.search("Lukawi Agent 框架", sources=["docs"])
        )
        assert len(results) >= 1
        assert any("Lukawi Agent" in r.content for r in results)

    def test_index_and_retrieve_conversation(self, rag_manager):
        conv_id = asyncio.run(
            rag_manager.index_conversation(
                "用户询问了 RAG 系统的工作原理",
                user_id="test_user",
                metadata={"topic": "RAG"},
            )
        )
        assert conv_id is not None
        results = asyncio.run(
            rag_manager.search(
                "RAG 工作原理",
                user_id="test_user",
                sources=["conversations"],
            )
        )
        assert len(results) >= 1

    def test_list_documents_shows_uploaded(self, rag_manager, sample_text_file):
        asyncio.run(rag_manager.upload_document(sample_text_file))
        docs = asyncio.run(rag_manager.list_documents())
        filenames = [d["filename"] for d in docs]
        assert "sample.txt" in filenames
