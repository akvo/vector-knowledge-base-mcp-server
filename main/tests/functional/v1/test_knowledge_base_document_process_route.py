import pytest

from unittest.mock import patch
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

    @patch("app.tasks.document_task.process_document_task.delay")
    async def test_process_documents_success(
        self,
        mock_delay,
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
        assert mock_delay.called

    @patch("app.tasks.document_task.process_document_task.delay")
    async def test_process_documents_skip_processing(
        self,
        mock_delay,
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
        assert not mock_delay.called

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

    async def test_list_documents_no_pagination(
        self,
        app: FastAPI,
        client: AsyncClient,
        api_key_value: str,
        session: Session,
    ):
        # Create KB
        kb = KnowledgeBase(name="KB1", description="Test KB")
        session.add(kb)
        session.commit()
        session.refresh(kb)

        # Add 2 documents
        doc1 = Document(
            file_path="/tmp/a.txt",
            file_name="a.txt",
            file_hash="a-hash",
            file_size=10,
            content_type="text/plain",
            knowledge_base_id=kb.id,
        )
        doc2 = Document(
            file_path="/tmp/b.txt",
            file_name="b.txt",
            file_hash="b-hash",
            file_size=12,
            content_type="text/plain",
            knowledge_base_id=kb.id,
        )
        session.add_all([doc1, doc2])
        session.commit()

        # Call endpoint without pagination wrapper
        res = await client.get(
            app.url_path_for("v1_list_kb_documents", kb_id=kb.id),
            headers=self.get_headers(api_key_value),
            params={"include_total": False},
        )

        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["file_name"] in ["a.txt", "b.txt"]

    async def test_list_documents_with_pagination(
        self,
        app: FastAPI,
        client: AsyncClient,
        api_key_value: str,
        session: Session,
    ):
        # Create KB
        kb = KnowledgeBase(name="KB2", description="Test KB 2")
        session.add(kb)
        session.commit()
        session.refresh(kb)

        # Create 3 documents
        for i in range(3):
            d = Document(
                file_path=f"/tmp/doc{i}.txt",
                file_name=f"doc{i}.txt",
                file_hash=f"doc{i}-hash",
                file_size=100,
                content_type="text/plain",
                knowledge_base_id=kb.id,
            )
            session.add(d)
        session.commit()

        # Call with pagination
        res = await client.get(
            app.url_path_for("v1_list_kb_documents", kb_id=kb.id),
            headers=self.get_headers(api_key_value),
            params={"include_total": True, "skip": 1, "limit": 1},
        )

        assert res.status_code == 200
        data = res.json()

        assert data["total"] == 3
        assert data["page"] == 2  # skip=1, limit=1 → page = 1//1 + 1 = 2
        assert data["size"] == 1
        assert len(data["data"]) == 1

    async def test_list_documents_search(
        self,
        app: FastAPI,
        client: AsyncClient,
        api_key_value: str,
        session: Session,
    ):
        # Create KB
        kb = KnowledgeBase(name="KB3", description="Search KB")
        session.add(kb)
        session.commit()
        session.refresh(kb)

        # Create docs
        docs = [
            Document(
                file_path="/tmp/alpha.txt",
                file_name="alpha.txt",
                file_hash="alpha-hash",
                file_size=10,
                content_type="text/plain",
                knowledge_base_id=kb.id,
            ),
            Document(
                file_path="/tmp/beta.txt",
                file_name="beta.txt",
                file_hash="beta-hash",
                file_size=20,
                content_type="text/plain",
                knowledge_base_id=kb.id,
            ),
        ]
        session.add_all(docs)
        session.commit()

        # Search
        res = await client.get(
            app.url_path_for("v1_list_kb_documents", kb_id=kb.id),
            headers=self.get_headers(api_key_value),
            params={"search": "alp"},
        )

        assert res.status_code == 200
        data = res.json()

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["file_name"] == "alpha.txt"

    async def test_list_documents_kb_isolation(
        self,
        app: FastAPI,
        client: AsyncClient,
        api_key_value: str,
        session: Session,
    ):
        # KB 1
        kb1 = KnowledgeBase(name="KB1", description="k1")
        session.add(kb1)
        session.commit()
        session.refresh(kb1)

        # KB 2
        kb2 = KnowledgeBase(name="KB2", description="k2")
        session.add(kb2)
        session.commit()
        session.refresh(kb2)

        # Documents in different KBs
        d1 = Document(
            file_path="/tmp/x.txt",
            file_name="x.txt",
            file_hash="x-hash",
            file_size=10,
            content_type="text/plain",
            knowledge_base_id=kb1.id,
        )
        d2 = Document(
            file_path="/tmp/y.txt",
            file_name="y.txt",
            file_hash="y-hash",
            file_size=20,
            content_type="text/plain",
            knowledge_base_id=kb2.id,
        )
        session.add_all([d1, d2])
        session.commit()

        # Request KB1 docs → must return ONLY doc1
        res = await client.get(
            app.url_path_for("v1_list_kb_documents", kb_id=kb1.id),
            headers=self.get_headers(api_key_value),
        )

        assert res.status_code == 200
        data = res.json()

        assert len(data) == 1
        assert data[0]["file_name"] == "x.txt"

    async def test_list_documents_empty(
        self,
        app: FastAPI,
        client: AsyncClient,
        api_key_value: str,
        session: Session,
    ):
        kb = KnowledgeBase(name="KBempty", description="No docs")
        session.add(kb)
        session.commit()
        session.refresh(kb)

        res = await client.get(
            app.url_path_for("v1_list_kb_documents", kb_id=kb.id),
            headers=self.get_headers(api_key_value),
        )

        assert res.status_code == 200
        data = res.json()

        assert data == []  # No pagination → plain list
