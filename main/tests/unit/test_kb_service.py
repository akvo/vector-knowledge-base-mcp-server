import pytest

from fastapi import HTTPException
from unittest.mock import MagicMock

from app.models.knowledge import KnowledgeBase
from app.services.kb_service import KnowledgeBaseService


@pytest.mark.unit
@pytest.mark.asyncio
class TestKnowledgeBaseService:
    async def test_delete_kb_not_found(self, session, patch_external_services):
        service = KnowledgeBaseService(session)

        with pytest.raises(HTTPException) as exc:
            await service.delete_kb(999)
        assert exc.value.status_code == 404
        assert "not found" in exc.value.detail

    async def test_delete_kb_success(self, session, patch_external_services):
        kb = KnowledgeBase(name="KB Delete", description="test")
        session.add(kb)
        session.commit()

        mock_minio = patch_external_services["mock_minio"]
        mock_vs = patch_external_services["mock_vector_store"]

        service = KnowledgeBaseService(session)
        result = await service.delete_kb(kb.id)

        assert "successfully" in result["message"]
        assert session.query(KnowledgeBase).filter_by(id=kb.id).first() is None
        mock_minio.list_objects.assert_called_once()
        mock_vs.delete_collection.assert_called_once()

    async def test_delete_kb_minio_failure(
        self, session, patch_external_services
    ):
        kb = KnowledgeBase(name="KB MinIOFail", description="test")
        session.add(kb)
        session.commit()

        mock_minio = patch_external_services["mock_minio"]
        mock_minio.list_objects.side_effect = Exception("MinIO boom")

        service = KnowledgeBaseService(session)
        result = await service.delete_kb(kb.id)

        assert "warnings" in result
        assert result["message"] == "KB deleted with warnings"
        assert "Unexpected MinIO cleanup error" in result["warnings"][0]
        assert session.query(KnowledgeBase).filter_by(id=kb.id).first() is None

    async def test_delete_kb_vector_store_failure(
        self, session, patch_external_services
    ):
        kb = KnowledgeBase(name="KB VecFail", description="test")
        session.add(kb)
        session.commit()

        mock_vs = patch_external_services["mock_vector_store"]
        mock_vs.delete_collection.side_effect = Exception("Vec boom")

        service = KnowledgeBaseService(session)
        result = await service.delete_kb(kb.id)

        assert "warnings" in result
        assert any(
            "Vector store cleanup failed" in w for w in result["warnings"]
        )
        assert session.query(KnowledgeBase).filter_by(id=kb.id).first() is None

    async def test_delete_kb_unexpected_failure(
        self, session, patch_external_services
    ):
        kb = KnowledgeBase(name="KB Fatal", description="test")
        session.add(kb)
        session.commit()

        # Force DB failure (simulating rollback or constraint issue)
        session.delete = MagicMock(side_effect=Exception("DB fatal"))

        service = KnowledgeBaseService(session)

        with pytest.raises(HTTPException) as exc:
            await service.delete_kb(kb.id)
        assert exc.value.status_code == 500
        assert "Failed to delete knowledge base: DB fatal" in exc.value.detail
