import pytest

from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.knowledge import (
    KnowledgeBase,
    DocumentUpload,
    ProcessingTask,
    Document,
)


@pytest.mark.asyncio
class TestGetProcessingTasksRoute:
    def get_headers(self, api_key_value: str):
        return {"Authorization": f"API-Key {api_key_value}"}

    async def test_get_tasks_unauthorized(
        self,
        app: FastAPI,
        client: AsyncClient,
    ):
        """Should return 401 if no API key provided"""
        res = await client.get(
            app.url_path_for("v1_get_processing_tasks", kb_id=1),
            params={"task_ids": "1,2"},
        )
        assert res.status_code == 401
        assert res.json()["detail"] == "API key required"

    async def test_get_tasks_success(
        self,
        app: FastAPI,
        session: Session,
        client: AsyncClient,
        api_key_value: str,
    ):
        """Should return multiple tasks with status info"""
        kb = KnowledgeBase(name="KB Task", description="desc")
        session.add(kb)
        session.commit()

        # buat uploads
        upload1 = DocumentUpload(
            knowledge_base_id=kb.id,
            file_name="doc1.txt",
            temp_path="tmp/doc1.txt",
            file_size=100,
            content_type="text/plain",
            file_hash="h111",
            status="pending",
        )
        upload2 = DocumentUpload(
            knowledge_base_id=kb.id,
            file_name="doc2.txt",
            temp_path="tmp/doc2.txt",
            file_size=200,
            content_type="text/plain",
            file_hash="h222",
            status="pending",
        )
        session.add_all([upload1, upload2])
        session.commit()

        # Create document
        doc1 = Document(
            knowledge_base_id=kb.id,
            file_name="doc1.txt",
            file_path=f"kb_{kb.id}/doc1.txt",
            file_size=100,
            content_type="text/plain",
            file_hash="h111",
        )
        session.add(doc1)
        session.commit()

        # Create task
        task1 = ProcessingTask(
            knowledge_base_id=kb.id,
            document_upload_id=upload1.id,
            status="completed",
            document_id=doc1.id,  # valid reference
        )
        task2 = ProcessingTask(
            knowledge_base_id=kb.id,
            document_upload_id=upload2.id,
            status="failed",
            error_message="Parse error",
        )
        session.add_all([task1, task2])
        session.commit()

        response = await client.get(
            app.url_path_for("v1_get_processing_tasks", kb_id=kb.id),
            headers=self.get_headers(api_key_value),
            params={"task_ids": f"{task1.id},{task2.id}"},
        )

        assert response.status_code == 200
        data = response.json()

        # check task1
        assert str(task1.id) in data
        assert data[str(task1.id)]["status"] == "completed"
        assert data[str(task1.id)]["file_name"] == "doc1.txt"

        # check task2
        assert str(task2.id) in data
        assert data[str(task2.id)]["status"] == "failed"
        assert data[str(task2.id)]["error_message"] == "Parse error"

    async def test_get_tasks_kb_not_found(
        self,
        app: FastAPI,
        client: AsyncClient,
        api_key_value: str,
    ):
        """Should return 404 if KB does not exist"""
        response = await client.get(
            app.url_path_for("v1_get_processing_tasks", kb_id=9999),
            headers=self.get_headers(api_key_value),
            params={"task_ids": "1,2"},
        )

        assert response.status_code == 404
        assert "Knowledge base not found" in response.text

    async def test_get_tasks_not_found_ids(
        self,
        app: FastAPI,
        session: Session,
        client: AsyncClient,
        api_key_value: str,
    ):
        """Should return empty dict if tasks not found"""
        kb = KnowledgeBase(name="KB Empty", description="desc")
        session.add(kb)
        session.commit()

        response = await client.get(
            app.url_path_for("v1_get_processing_tasks", kb_id=kb.id),
            headers=self.get_headers(api_key_value),
            params={"task_ids": "11111,22222"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data == {}
