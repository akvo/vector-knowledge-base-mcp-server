import pytest

from app.models.knowledge import KnowledgeBase, DocumentUpload


@pytest.mark.asyncio
class TestGetKBDocuments:
    """🧪 Tests for GET /{kb_id}/documents endpoint"""

    def get_headers(self, api_key_value: str):
        return {"Authorization": f"API-Key {api_key_value}"}

    async def test_get_kb_documents_success(
        self, app, client, session, api_key_value
    ):
        """✅ Should return all documents belonging to a KB"""
        kb = KnowledgeBase(name="Docs KB", description="For listing test")
        session.add(kb)
        session.commit()

        docs = [
            DocumentUpload(
                knowledge_base_id=kb.id,
                file_name="file1.txt",
                file_hash="hash1",
                file_size=123,
                content_type="text/plain",
                temp_path="/tmp/file1.txt",
                status="processed",
            ),
            DocumentUpload(
                knowledge_base_id=kb.id,
                file_name="file2.txt",
                file_hash="hash2",
                file_size=456,
                content_type="text/plain",
                temp_path="/tmp/file2.txt",
                status="pending",
            ),
        ]
        session.add_all(docs)
        session.commit()

        res = await client.get(
            app.url_path_for("v1_get_kb_documents_upload", kb_id=kb.id),
            headers=self.get_headers(api_key_value),
        )

        assert res.status_code == 200

        data = res.json()
        assert isinstance(data, list)
        assert len(data) == 2

        filenames = {d["file_name"] for d in data}
        assert filenames == {"file1.txt", "file2.txt"}

        statuses = {d["status"] for d in data}
        assert statuses == {"processed", "pending"}

    async def test_get_kb_documents_not_found(
        self, app, client, api_key_value
    ):
        """❌ Should return 404 if KB does not exist"""
        res = await client.get(
            app.url_path_for("v1_get_kb_documents_upload", kb_id=9999),
            headers=self.get_headers(api_key_value),
        )

        assert res.status_code == 404
        assert res.json()["detail"] == "Knowledge base not found"

    async def test_get_kb_documents_empty_list(
        self, app, client, session, api_key_value
    ):
        """✅ Should return empty list if KB exists but no documents"""
        kb = KnowledgeBase(name="Empty KB", description="KB with no docs")
        session.add(kb)
        session.commit()

        res = await client.get(
            app.url_path_for("v1_get_kb_documents_upload", kb_id=kb.id),
            headers=self.get_headers(api_key_value),
        )

        assert res.status_code == 200
        data = res.json()
        assert data == []
