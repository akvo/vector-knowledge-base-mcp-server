import pytest
import json
import base64

from unittest.mock import AsyncMock
from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeBase, Document
from app.services.kb_query_service import query_vector_kbs


@pytest.mark.asyncio
class TestQueryVectorKbsIntegration:
    async def test_kb_not_found(self):
        """Should return note if no KB found"""
        res = await query_vector_kbs("hello", [9999], top_k=3)
        assert res["context"] is None
        assert "No active knowledge base" in res["note"]

    async def test_kb_empty(self, session: Session):
        """Should return note if KB exists but has no documents"""
        kb = KnowledgeBase(name="KB Empty", description="desc")
        session.add(kb)
        session.commit()

        res = await query_vector_kbs("hello", [kb.id], top_k=3)
        assert res["context"] is None
        assert f"Knowledge base {kb.id} is empty." in res["note"]

    async def test_success_retrieval(
        self, session: Session, patch_query_services
    ):
        """Should return encoded context if retrieval works"""
        _, mock_store = patch_query_services

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

        # Mock retriever with AsyncMock
        mock_retriever = AsyncMock()
        mock_retriever.aget_relevant_documents.return_value = [
            type(
                "Doc",
                (),
                {"page_content": "mock content", "metadata": {"id": 1}},
            )()
        ]
        mock_store.as_retriever.return_value = mock_retriever

        res = await query_vector_kbs("hello", [kb.id], top_k=2)

        assert res["context"] is not None
        decoded = json.loads(base64.b64decode(res["context"]).decode())
        assert decoded["context"][0]["page_content"] == "mock content"
        assert decoded["context"][0]["metadata"]["id"] == 1

    async def test_internal_error(
        self, session: Session, patch_query_services
    ):
        """Should handle exceptions gracefully"""
        _, mock_store = patch_query_services

        kb = KnowledgeBase(name="KB Error", description="desc")
        session.add(kb)
        session.commit()

        # Document
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

        # Force error
        mock_store.as_retriever.side_effect = Exception("Vector store failed")

        res = await query_vector_kbs("hello", [kb.id], top_k=2)

        assert res["context"] is None
        assert "Vector store failed" in res["note"]
