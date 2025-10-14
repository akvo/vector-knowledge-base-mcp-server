import io
import pytest

from fastapi import status
from app.models.knowledge import KnowledgeBase


@pytest.mark.asyncio
class TestFullProcessKBDocuments:
    def get_headers(self, api_key_value: str):
        return {"Authorization": f"API-Key {api_key_value}"}

    async def test_full_process_requires_api_key(self, app, client, session):
        """No API key should return 401"""
        kb = KnowledgeBase(name="NoAuth KB", description="KB no API key")
        session.add(kb)
        session.commit()

        files = [("files", ("test.txt", io.BytesIO(b"no auth"), "text/plain"))]

        res = await client.post(
            app.url_path_for("v1_full_process_documents", kb_id=kb.id),
            files=files,
        )

        assert res.status_code == status.HTTP_401_UNAUTHORIZED
        assert res.json()["detail"] == "API key required"

    async def test_full_process_success(
        self,
        app,
        client,
        session,
        api_key_value,
        patch_external_services,
        patch_document_service,
    ):
        """✅ Should upload and process documents successfully"""
        kb = KnowledgeBase(name="Full KB", description="KB for full process")
        session.add(kb)
        session.commit()
        kb_id = kb.id

        files = [
            (
                "files",
                ("full.txt", io.BytesIO(b"some text content"), "text/plain"),
            )
        ]

        res = await client.post(
            app.url_path_for("v1_full_process_documents", kb_id=kb_id),
            headers=self.get_headers(api_key_value),
            files=files,
        )

        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["message"] == "Documents accepted for processing"
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["status"] == "pending"

        # Optional: verify the mock was called
        patch_document_service.upload_documents.assert_awaited_once()
        patch_document_service.process_documents.assert_awaited_once()

    async def test_full_process_upload_error(
        self,
        app,
        client,
        session,
        api_key_value,
        patch_external_services,
        patch_document_service,
    ):
        """❌ Upload phase raises exception"""
        kb = KnowledgeBase(name="Err KB", description="KB with upload error")
        session.add(kb)
        session.commit()

        patch_document_service.upload_documents.side_effect = Exception(
            "upload failed"
        )

        files = [
            ("files", ("err.txt", io.BytesIO(b"err content"), "text/plain"))
        ]

        res = await client.post(
            app.url_path_for("v1_full_process_documents", kb_id=kb.id),
            headers=self.get_headers(api_key_value),
            files=files,
        )

        assert res.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "upload failed" in res.json()["detail"].lower()
