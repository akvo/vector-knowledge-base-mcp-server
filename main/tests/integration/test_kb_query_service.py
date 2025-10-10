import pytest
import json
import base64

from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
from app.models.knowledge import KnowledgeBase, Document
from app.services.kb_query_service import query_vector_kbs


@pytest.mark.asyncio
class TestQueryVectorKbsIntegration:
    async def test_kb_not_found(self, patch_external_services):
        """Should return note if no KB found"""
        res = await query_vector_kbs("hello", [9999], top_k=3)
        assert res["context"] is not None
        decoded = json.loads(base64.b64decode(res["context"]).decode())
        assert decoded["context"] == []
        assert "No active knowledge base" in res["note"]

    async def test_kb_empty(self, session: Session, patch_external_services):
        """Should return note if KB exists but has no documents"""
        kb = KnowledgeBase(name="KB Empty", description="desc")
        session.add(kb)
        session.commit()

        res = await query_vector_kbs("hello", [kb.id], top_k=3)

        assert res["context"] is not None
        decoded = json.loads(base64.b64decode(res["context"]).decode())
        assert decoded["context"] == []
        assert "No relevant documents" in res["note"]

    async def test_success_retrieval(self, session: Session):
        """Should return encoded context if retrieval works"""
        kb = KnowledgeBase(name="KB Retrieval", description="desc")
        session.add(kb)
        session.commit()

        doc = Document(
            knowledge_base_id=kb.id,
            file_path="docs/test1.pdf",
            file_name="test1.pdf",
            file_size=1024,
            content_type="application/pdf",
            file_hash="hash123abc",
        )
        session.add(doc)
        session.commit()

        # Mock Chroma and EmbeddingsFactory
        with patch(
            "app.services.kb_query_service.ChromaVectorStore"
        ) as mock_store, patch(
            "app.services.kb_query_service.EmbeddingsFactory"
        ) as mock_embed:

            mock_embed.create.return_value = MagicMock()
            mock_vector = MagicMock()
            mock_store.return_value = mock_vector

            # Mock results from similarity search
            mock_doc = MagicMock()
            mock_doc.page_content = "mock content"
            mock_doc.metadata = {"id": 1, "title": "Mock Document"}
            mock_vector.similarity_search_with_score.return_value = [
                (mock_doc, 0.1)
            ]

            res = await query_vector_kbs("hello", [kb.id], top_k=2)

        assert res["context"] is not None
        decoded = json.loads(base64.b64decode(res["context"]).decode())
        assert decoded["context"][0]["page_content"] == "mock content"
        assert decoded["context"][0]["metadata"]["id"] == 1

    async def test_internal_error(
        self, session: Session, patch_external_services
    ):
        kb = KnowledgeBase(name="KB Error", description="desc")
        session.add(kb)
        session.commit()

        doc = Document(
            knowledge_base_id=kb.id,
            file_path="docs/error.pdf",
            file_name="error.pdf",
            file_size=2048,
            content_type="application/pdf",
            file_hash="hash456def",
        )
        session.add(doc)
        session.commit()

        # Override the fixture’s vector store behavior
        patch_external_services[
            "mock_vector_store"
        ].similarity_search_with_score.side_effect = Exception(
            "Vector store failed"
        )

        res = await query_vector_kbs("hello", [kb.id], top_k=2)

        assert res["context"] is not None
        decoded = json.loads(base64.b64decode(res["context"]).decode())
        assert decoded["context"] == []
        assert (
            "No relevant documents found across selected KBs." in res["note"]
        )
