import pytest

from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeBase, Document


@pytest.mark.asyncio
class TestGetDocumentRoute:
    def get_headers(self, api_key_value: str):
        return {"Authorization": f"API-Key {api_key_value}"}

    async def test_get_document_unauthorized(
        self, app: FastAPI, client: AsyncClient
    ):
        """Should return 401 if no API key provided"""
        res = await client.get(
            app.url_path_for("v1_get_document", kb_id=1, doc_id=1)
        )
        assert res.status_code == 401
        assert res.json()["detail"] == "API key required"

    async def test_get_document_success(
        self,
        app: FastAPI,
        session: Session,
        client: AsyncClient,
        api_key_value: str,
    ):
        """Should return document details if found"""
        kb = KnowledgeBase(name="KB Docs", description="desc")
        session.add(kb)
        session.commit()

        doc = Document(
            knowledge_base_id=kb.id,
            file_name="manual.pdf",
            file_path=f"kb_{kb.id}/manual.pdf",
            file_size=1024,
            content_type="application/pdf",
            file_hash="abc123",
        )
        session.add(doc)
        session.commit()

        res = await client.get(
            app.url_path_for("v1_get_document", kb_id=kb.id, doc_id=doc.id),
            headers=self.get_headers(api_key_value),
        )

        assert res.status_code == 200
        data = res.json()
        assert data["id"] == doc.id
        assert data["file_name"] == "manual.pdf"
        assert data["knowledge_base_id"] == kb.id

    async def test_get_document_not_found_in_kb(
        self,
        app: FastAPI,
        session: Session,
        client: AsyncClient,
        api_key_value: str,
    ):
        """Should return 404 if document does not exist in given KB"""
        kb = KnowledgeBase(name="KB Empty", description="desc")
        session.add(kb)
        session.commit()

        res = await client.get(
            app.url_path_for("v1_get_document", kb_id=kb.id, doc_id=9999),
            headers=self.get_headers(api_key_value),
        )
        assert res.status_code == 404
        assert res.json()["detail"] == "Document not found"

    async def test_get_document_kb_not_found(
        self, app: FastAPI, client: AsyncClient, api_key_value: str
    ):
        """Should return 404 if KB does not exist at all"""
        res = await client.get(
            app.url_path_for("v1_get_document", kb_id=9999, doc_id=1),
            headers=self.get_headers(api_key_value),
        )
        assert res.status_code == 404
        assert res.json()["detail"] == "Document not found"
