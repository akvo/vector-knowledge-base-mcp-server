import pytest

from fastapi import status
from minio.error import S3Error as MinioException

from app.core.config import settings
from app.models.knowledge import KnowledgeBase


@pytest.mark.asyncio
class TestDeleteKnowledgeBase:
    def get_headers(self, api_key_value: str):
        return {"Authorization": f"API-Key {api_key_value}"}

    async def test_delete_kb_requires_api_key(
        self, app, session, client, patch_kb_route_services
    ):
        """No API key should return 401"""
        kb = KnowledgeBase(name="Test KB", description="A test KB")
        session.add(kb)
        session.commit()
        kb_id = kb.id

        mock_minio, mock_vector, _, _ = patch_kb_route_services
        mock_minio.list_objects.return_value = []

        res = await client.delete(
            app.url_path_for("v1_delete_knowledge_base", kb_id=kb_id),
        )
        assert res.status_code == 401
        assert res.json()["detail"] == "API key required"

    async def test_delete_success(
        self,
        client,
        app,
        session,
        api_key_value,
        patch_kb_route_services,
    ):
        kb = KnowledgeBase(name="Test KB", description="A test KB")
        session.add(kb)
        session.commit()
        kb_id = kb.id

        mock_minio, mock_vector, _, _ = patch_kb_route_services
        mock_minio.list_objects.return_value = []

        response = await client.delete(
            app.url_path_for("v1_delete_knowledge_base", kb_id=kb_id),
            headers=self.get_headers(api_key_value),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "message": "KB and all associated resources deleted successfully"
        }

        mock_minio.list_objects.assert_called_once_with(
            settings.minio_bucket_name, prefix=f"kb_{kb_id}/"
        )
        mock_vector.delete_collection.assert_called_once()
        assert session.query(KnowledgeBase).filter_by(id=kb_id).first() is None

    async def test_delete_kb_not_found(self, client, app, api_key_value):
        response = await client.delete(
            app.url_path_for("v1_delete_knowledge_base", kb_id=999999),
            headers=self.get_headers(api_key_value),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "Knowledge base not found"}

    async def test_delete_minio_error(
        self,
        client,
        app,
        session,
        api_key_value,
        patch_kb_route_services,
    ):
        kb = KnowledgeBase(name="Test KB 2", description="A test KB 2")
        session.add(kb)
        session.commit()
        kb_id = kb.id

        mock_minio, _, _, _ = patch_kb_route_services
        mock_minio.list_objects.side_effect = MinioException(
            code="500",
            message="MinIO down",
            resource="test-resource",
            request_id="req-123",
            host_id="host-123",
            response=None,
        )

        response = await client.delete(
            app.url_path_for("v1_delete_knowledge_base", kb_id=kb_id),
            headers=self.get_headers(api_key_value),
        )

        assert response.status_code == status.HTTP_200_OK
        assert "warnings" in response.json()
        assert (
            "Failed to clean up MinIO files" in response.json()["warnings"][0]
        )
        assert session.query(KnowledgeBase).filter_by(id=kb_id).first() is None

    async def test_delete_chroma_error(
        self,
        client,
        app,
        session,
        api_key_value,
        patch_kb_route_services,
    ):
        kb = KnowledgeBase(name="Test KB 3", description="A test KB 3")
        session.add(kb)
        session.commit()
        kb_id = kb.id

        mock_minio, mock_vector, _, _ = patch_kb_route_services
        mock_minio.list_objects.return_value = []
        mock_vector.delete_collection.side_effect = Exception("Chroma down")

        response = await client.delete(
            app.url_path_for("v1_delete_knowledge_base", kb_id=kb_id),
            headers=self.get_headers(api_key_value),
        )

        assert response.status_code == status.HTTP_200_OK
        assert "warnings" in response.json()
        assert (
            "Failed to clean up vector store" in response.json()["warnings"][0]
        )
        assert session.query(KnowledgeBase).filter_by(id=kb_id).first() is None

    async def test_delete_unexpected_exception(
        self,
        client,
        app,
        session,
        api_key_value,
        patch_kb_route_services,
    ):
        kb = KnowledgeBase(name="Test KB 4", description="A test KB 4")
        session.add(kb)
        session.commit()
        kb_id = kb.id

        mock_minio, mock_vector, _, _ = patch_kb_route_services
        mock_minio.list_objects.return_value = []
        # simulate unexpected failure
        mock_minio.list_objects.side_effect = RuntimeError("Unexpected error")

        response = await client.delete(
            app.url_path_for("v1_delete_knowledge_base", kb_id=kb_id),
            headers=self.get_headers(api_key_value),
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == {
            "detail": "Failed to delete knowledge base: Unexpected error"
        }

        # KB tetap terhapus dari DB
        assert (
            session.query(KnowledgeBase).filter_by(id=kb_id).first()
            is not None
        )
