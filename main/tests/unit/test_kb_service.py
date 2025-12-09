import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock

from app.models.knowledge import KnowledgeBase
from app.services.kb_service import KnowledgeBaseService


@pytest.mark.unit
@pytest.mark.asyncio
class TestKnowledgeBaseService:

    # DELETE KB (DB deletion only)
    async def test_delete_kb_not_found(self, session, patch_external_services):
        service = KnowledgeBaseService(session)

        with pytest.raises(HTTPException) as exc:
            service.delete_kb_record_only(999)

        assert exc.value.status_code == 404
        assert "not found" in exc.value.detail.lower()

    async def test_delete_kb_record_only_success(
        self, session, patch_external_services
    ):
        kb = KnowledgeBase(name="KB Delete", description="test")
        session.add(kb)
        session.commit()

        service = KnowledgeBaseService(session)
        service.delete_kb_record_only(kb.id)

        assert session.query(KnowledgeBase).filter_by(id=kb.id).first() is None

    async def test_delete_kb_record_only_db_failure(
        self, session, patch_external_services
    ):
        kb = KnowledgeBase(name="KB Fatal", description="test")
        session.add(kb)
        session.commit()

        session.delete = MagicMock(side_effect=Exception("DB fatal"))

        service = KnowledgeBaseService(session)

        with pytest.raises(HTTPException) as exc:
            service.delete_kb_record_only(kb.id)

        assert exc.value.status_code == 500
        assert "DB fatal" in exc.value.detail

    # CLEANUP TESTS
    async def test_cleanup_success(self, session, patch_external_services):
        kb_id = 123

        mock_minio = patch_external_services["mock_minio"]
        mock_vs = patch_external_services["mock_vector_store"]

        service = KnowledgeBaseService(session)
        service.cleanup_kb_resources(kb_id)

        mock_minio.list_objects.assert_called_once()
        mock_vs.delete_collection.assert_called_once()

    async def test_cleanup_minio_failure(
        self, session, patch_external_services
    ):
        kb_id = 456
        mock_minio = patch_external_services["mock_minio"]
        mock_minio.list_objects.side_effect = Exception("MinIO boom")

        service = KnowledgeBaseService(session)

        with pytest.raises(Exception) as exc:
            service.cleanup_kb_resources(kb_id)

        assert "MinIO boom" in str(exc.value)

    async def test_cleanup_vector_store_failure(
        self, session, patch_external_services
    ):
        kb_id = 789
        mock_vs = patch_external_services["mock_vector_store"]
        mock_vs.delete_collection.side_effect = Exception("Vec boom")

        service = KnowledgeBaseService(session)

        with pytest.raises(Exception) as exc:
            service.cleanup_kb_resources(kb_id)

        assert "Vec boom" in str(exc.value)
