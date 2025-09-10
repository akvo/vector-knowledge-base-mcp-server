import pytest

from unittest.mock import patch
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeBase, DocumentUpload, ProcessingTask


@pytest.mark.asyncio
class TestProcessDocumentsRoute:
    def get_headers(self, api_key_value: str):
        return {"Authorization": f"API-Key {api_key_value}"}

    async def test_process_documents_unauthorized(
        self,
        app: FastAPI,
        client: AsyncClient,
    ):
        """Should return 401 if no API key is provided"""
        # No Authorization header
        res = await client.post(
            app.url_path_for("v1_process_kb_documents", kb_id=1),
            json=[{"upload_id": 1}],
        )

        assert res.status_code == 401
        assert res.json()["detail"] == "API key required"

    @patch("app.api.v1.knowledge_base.router.add_processing_tasks_to_queue")
    async def test_process_documents_success(
        self,
        mock_add_queue,
        app: FastAPI,
        session: Session,
        client: AsyncClient,
        api_key_value: str,
    ):
        """Process route should create tasks for uploads"""
        kb = KnowledgeBase(name="KB Proc", description="desc")
        session.add(kb)
        session.commit()

        upload = DocumentUpload(
            knowledge_base_id=kb.id,
            file_name="doc.txt",
            temp_path="tmp/doc.txt",
            file_size=123,
            content_type="text/plain",
            file_hash="h123",
            status="pending",
        )
        session.add(upload)
        session.commit()

        response = await client.post(
            app.url_path_for("v1_process_kb_documents", kb_id=kb.id),
            headers=self.get_headers(api_key_value),
            json=[{"upload_id": upload.id}],
        )

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert any(t["upload_id"] == upload.id for t in data["tasks"])

        # check DB
        task = session.query(ProcessingTask).first()
        assert task is not None
        assert task.document_upload_id == upload.id
        assert task.status == "pending"

        # background task must be queued
        assert mock_add_queue.called

    @patch("app.api.v1.knowledge_base.router.add_processing_tasks_to_queue")
    async def test_process_documents_skip_processing(
        self,
        mock_add_queue,
        app: FastAPI,
        session: Session,
        client: AsyncClient,
        api_key_value: str,
    ):
        """Skip processing should return empty tasks"""
        kb = KnowledgeBase(name="KB Skip", description="desc")
        session.add(kb)
        session.commit()

        upload = DocumentUpload(
            knowledge_base_id=kb.id,
            file_name="skip.txt",
            temp_path="tmp/skip.txt",
            file_size=123,
            content_type="text/plain",
            file_hash="h999",
            status="pending",
        )
        session.add(upload)
        session.commit()

        response = await client.post(
            app.url_path_for("v1_process_kb_documents", kb_id=kb.id),
            headers=self.get_headers(api_key_value),
            json=[{"upload_id": upload.id, "skip_processing": True}],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tasks"] == []
        assert not mock_add_queue.called

    async def test_process_documents_kb_not_found(
        self,
        app: FastAPI,
        client: AsyncClient,
        api_key_value: str,
    ):
        """Should return 404 if KB not found"""
        response = await client.post(
            app.url_path_for("v1_process_kb_documents", kb_id=99999),
            headers=self.get_headers(api_key_value),
            json=[{"upload_id": 1}],
        )

        assert response.status_code == 404
        assert "Knowledge base not found" in response.text
