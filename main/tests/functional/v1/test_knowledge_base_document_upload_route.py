import io
import pytest

from fastapi import status
from minio.error import S3Error as MinioException

from app.models.knowledge import KnowledgeBase, Document, DocumentUpload


@pytest.mark.asyncio
class TestUploadKBDocuments:
    def get_headers(self, api_key_value: str):
        return {"Authorization": f"API-Key {api_key_value}"}

    async def test_upload_kb_requires_api_key(self, app, session, client):
        """No API key should return 401"""
        # Arrange KB
        kb = KnowledgeBase(name="Single KB", description="KB for single doc")
        session.add(kb)
        session.commit()
        kb_id = kb.id

        file_content = b"hello world"
        files = [
            ("files", ("test.txt", io.BytesIO(file_content), "text/plain")),
        ]

        res = await client.post(
            app.url_path_for("v1_upload_kb_documents", kb_id=kb_id),
            files=files,
        )
        assert res.status_code == 401
        assert res.json()["detail"] == "API key required"

    async def test_upload_single_document(
        self, client, app, session, api_key_value, patch_kb_route_services
    ):
        # Arrange KB
        kb = KnowledgeBase(name="Single KB", description="KB for single doc")
        session.add(kb)
        session.commit()
        kb_id = kb.id

        file_content = b"hello world"
        files = [
            ("files", ("test.txt", io.BytesIO(file_content), "text/plain")),
        ]

        # Act
        response = await client.post(
            app.url_path_for("v1_upload_kb_documents", kb_id=kb_id),
            headers=self.get_headers(api_key_value),
            files=files,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "pending"
        assert data[0]["skip_processing"] is False
        assert data[0]["file_name"] == "test.txt"

        # DB check
        uploads = session.query(DocumentUpload).all()
        assert len(uploads) == 1
        assert uploads[0].file_name == "test.txt"
        assert uploads[0].knowledge_base_id == kb_id

    async def test_upload_multiple_documents(
        self, client, app, session, api_key_value, patch_kb_route_services
    ):
        kb = KnowledgeBase(
            name="Multi KB", description="KB with multiple docs"
        )
        session.add(kb)
        session.commit()
        kb_id = kb.id

        file1_content = b"hello world"
        file2_content = b"another content"

        files = [
            ("files", ("file1.txt", io.BytesIO(file1_content), "text/plain")),
            ("files", ("file2.txt", io.BytesIO(file2_content), "text/plain")),
        ]

        response = await client.post(
            app.url_path_for("v1_upload_kb_documents", kb_id=kb_id),
            headers=self.get_headers(api_key_value),
            files=files,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        filenames = [item["file_name"] for item in data]
        assert "file1.txt" in filenames
        assert "file2.txt" in filenames

        # DB check
        uploads = (
            session.query(DocumentUpload)
            .filter(DocumentUpload.knowledge_base_id == kb_id)
            .all()
        )
        assert len(uploads) == 2

    async def test_upload_duplicate_document(
        self, client, app, session, api_key_value, patch_kb_route_services
    ):
        kb = KnowledgeBase(name="Dup KB", description="KB with duplicate doc")
        session.add(kb)
        session.commit()
        kb_id = kb.id

        file_content = b"duplicate content"
        file_hash = (
            "b79f8c07798dcc75d6f288e6a620644a88a9c67e74019a57b88a5bfd918e4b0f"
        )

        # Existing document
        existing_doc = Document(
            file_path="kb_1/docs/dup.txt",
            file_name="dup.txt",
            file_size=len(file_content),
            content_type="text/plain",
            file_hash=file_hash,
            knowledge_base_id=kb_id,
        )
        session.add(existing_doc)
        session.commit()

        files = [
            ("files", ("dup.txt", io.BytesIO(file_content), "text/plain")),
        ]

        response = await client.post(
            app.url_path_for("v1_upload_kb_documents", kb_id=kb_id),
            headers=self.get_headers(api_key_value),
            files=files,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "exists"
        assert data[0]["skip_processing"] is True
        assert data[0]["file_name"] == "dup.txt"

    async def test_upload_kb_not_found(
        self, client, app, api_key_value, patch_kb_route_services
    ):
        files = [
            ("files", ("nofile.txt", io.BytesIO(b"abc"), "text/plain")),
        ]

        response = await client.post(
            app.url_path_for("v1_upload_kb_documents", kb_id=9999),
            headers=self.get_headers(api_key_value),
            files=files,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "Knowledge base not found"}

    async def test_upload_minio_error(
        self, client, app, session, api_key_value, patch_kb_route_services
    ):
        kb = KnowledgeBase(name="Err KB", description="KB with Minio error")
        session.add(kb)
        session.commit()
        kb_id = kb.id

        file_content = b"content"
        files = [
            ("files", ("err.txt", io.BytesIO(file_content), "text/plain")),
        ]

        mock_minio, _, _ = patch_kb_route_services
        mock_minio.put_object.side_effect = MinioException(
            code="500",
            message="MinIO down",
            resource="upload",
            request_id="req-123",
            host_id="host-123",
            response=None,
        )

        response = await client.post(
            app.url_path_for("v1_upload_kb_documents", kb_id=kb_id),
            headers=self.get_headers(api_key_value),
            files=files,
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == {"detail": "Failed to upload file"}
