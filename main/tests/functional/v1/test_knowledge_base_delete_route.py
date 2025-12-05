import pytest

from unittest.mock import patch
from app.models.knowledge import KnowledgeBase, ProcessingTask


@pytest.mark.asyncio
class TestDeleteKnowledgeBase:
    def get_headers(self, api_key_value: str):
        return {"Authorization": f"API-Key {api_key_value}"}

    async def test_delete_kb_requires_api_key(
        self, app, session, client, patch_external_services
    ):
        """No API key should return 401"""
        kb = KnowledgeBase(name="Test KB", description="A test KB")
        session.add(kb)
        session.commit()
        kb_id = kb.id

        mock_minio = patch_external_services["mock_minio"]
        mock_minio.list_objects.return_value = []

        res = await client.delete(
            app.url_path_for("v1_delete_knowledge_base", kb_id=kb_id),
        )
        assert res.status_code == 401
        assert res.json()["detail"] == "API key required"

    @patch("app.api.v1.knowledge_base.kb_router.cleanup_kb_task.delay")
    async def test_delete_success(
        self,
        mock_delay,
        client,
        app,
        session,
        api_key_value,
        patch_external_services,
    ):
        # Return a real string as Celery task ID
        mock_delay.return_value.id = "fake-celery-task-id-123"

        kb = KnowledgeBase(name="Test KB", description="A test KB")
        session.add(kb)
        session.commit()
        kb_id = kb.id

        response = await client.delete(
            app.url_path_for("v1_delete_knowledge_base", kb_id=kb_id),
            headers=self.get_headers(api_key_value),
        )

        assert response.status_code == 200
        assert response.json() == {
            "message": "Knowledge base deleted. Cleanup scheduled.",
            "kb_id": kb_id,
        }
        assert mock_delay.called
        assert session.query(KnowledgeBase).filter_by(id=kb_id).first() is None
        # Confirm that the DB now has the string, not MagicMock
        task_record = (
            session.query(ProcessingTask)
            .filter(ProcessingTask.celery_task_id == "fake-celery-task-id-123")
            .first()
        )
        assert task_record is not None

    async def test_delete_kb_not_found(self, client, app, api_key_value):
        response = await client.delete(
            app.url_path_for("v1_delete_knowledge_base", kb_id=999999),
            headers=self.get_headers(api_key_value),
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "Knowledge base not found"}
