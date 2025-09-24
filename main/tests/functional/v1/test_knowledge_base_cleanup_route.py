import pytest

from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from minio.error import S3Error as MinioException

from app.core.config import settings
from app.models.knowledge import KnowledgeBase, DocumentUpload


@pytest.mark.asyncio
class TestCleanupTempFilesRoute:
    def get_headers(self, api_key_value: str):
        return {"Authorization": f"API-Key {api_key_value}"}

    async def test_cleanup_temp_files_unauthorized(
        self,
        app: FastAPI,
        client: AsyncClient,
    ):
        """Should return 401 if no API key is provided"""
        res = await client.post(app.url_path_for("v1_cleanup_temp_files"))
        assert res.status_code == 401
        assert res.json()["detail"] == "API key required"

    async def test_cleanup_temp_files_success(
        self,
        app: FastAPI,
        session: Session,
        client: AsyncClient,
        api_key_value: str,
        patch_kb_route_services,
    ):
        """Expired uploads should be deleted from DB and MinIO"""
        mock_minio, _, _, _ = patch_kb_route_services

        kb = KnowledgeBase(name="KB Cleanup", description="desc")
        session.add(kb)
        session.commit()

        # expired upload
        expired_upload = DocumentUpload(
            knowledge_base_id=kb.id,
            file_name="old.txt",
            temp_path="tmp/old.txt",
            file_size=100,
            content_type="text/plain",
            file_hash="h123",
            status="pending",
            created_at=datetime.utcnow() - timedelta(days=2),
        )
        session.add(expired_upload)

        # fresh upload (should not be deleted)
        fresh_upload = DocumentUpload(
            knowledge_base_id=kb.id,
            file_name="new.txt",
            temp_path="tmp/new.txt",
            file_size=50,
            content_type="text/plain",
            file_hash="h456",
            status="pending",
            created_at=datetime.utcnow(),
        )
        session.add(fresh_upload)
        session.commit()

        # save IDs before commit
        expired_id = expired_upload.id
        fresh_id = fresh_upload.id

        response = await client.post(
            app.url_path_for("v1_cleanup_temp_files"),
            headers=self.get_headers(api_key_value),
        )

        assert response.status_code == 200
        data = response.json()
        assert "Cleaned up" in data["message"]

        # expired deleted
        assert (
            session.query(DocumentUpload).filter_by(id=expired_id).first()
            is None
        )
        # fresh still exists
        assert (
            session.query(DocumentUpload).filter_by(id=fresh_id).first()
            is not None
        )
        # MinIO deletion called
        mock_minio.remove_object.assert_called_once_with(
            bucket_name=settings.minio_bucket_name, object_name="tmp/old.txt"
        )

    async def test_cleanup_temp_files_minio_failure(
        self,
        app: FastAPI,
        session: Session,
        client: AsyncClient,
        api_key_value: str,
        patch_kb_route_services,
    ):
        """
        Expired uploads should still be removed from DB even if MinIO deletion
        fails
        """
        mock_minio, _, _, _ = patch_kb_route_services

        kb = KnowledgeBase(name="KB Cleanup2", description="desc")
        session.add(kb)
        session.commit()

        expired_upload = DocumentUpload(
            knowledge_base_id=kb.id,
            file_name="bad.txt",
            temp_path="tmp/bad.txt",
            file_size=200,
            content_type="text/plain",
            file_hash="h789",
            status="pending",
            created_at=datetime.utcnow() - timedelta(days=3),
        )
        session.add(expired_upload)
        session.commit()

        # save ID before commit
        expired_id = expired_upload.id

        mock_minio.remove_object.side_effect = MinioException(
            code="500",
            message="MinIO failed",
            resource="test-resource",
            request_id="req-123",
            host_id="host-123",
            response=None,
        )

        response = await client.post(
            app.url_path_for("v1_cleanup_temp_files"),
            headers=self.get_headers(api_key_value),
        )

        assert response.status_code == 200
        data = response.json()
        assert "Cleaned up" in data["message"]

        # expired upload deleted from DB anyway
        assert (
            session.query(DocumentUpload).filter_by(id=expired_id).first()
            is None
        )
        # minio deletion attempted
        mock_minio.remove_object.assert_called_once_with(
            bucket_name=settings.minio_bucket_name, object_name="tmp/bad.txt"
        )
