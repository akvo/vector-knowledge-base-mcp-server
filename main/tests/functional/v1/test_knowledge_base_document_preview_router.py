import pytest

from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeBase, Document, DocumentUpload


@pytest.mark.asyncio
class TestPreviewDocumentsRoute:
    def get_headers(self, api_key_value: str):
        return {"Authorization": f"API-Key {api_key_value}"}

    async def test_preview_unauthorized(
        self,
        app: FastAPI,
        session: Session,
        client: AsyncClient,
    ):
        """Preview route should return 401 if no API key is provided"""
        kb = KnowledgeBase(name="KB Unauthorized", description="desc")
        session.add(kb)
        session.commit()

        res = await client.post(
            app.url_path_for("v1_preview_kb_documents", kb_id=kb.id),
            json={
                "document_ids": [1],
                "chunk_size": 50,
                "chunk_overlap": 0,
            },
        )

        assert res.status_code == 401
        assert res.json()["detail"] == "API key required"

    async def test_preview_with_document(
        self,
        app: FastAPI,
        session: Session,
        client: AsyncClient,
        api_key_value: str,
        patch_external_services,
    ):
        """Preview route should work with existing Document"""
        kb = KnowledgeBase(name="KB Test", description="desc")
        session.add(kb)
        session.commit()

        doc = Document(
            knowledge_base_id=kb.id,
            file_name="doc.txt",
            file_path=f"kb_{kb.id}/doc.txt",
            file_size=10,
            content_type="text/plain",
            file_hash="hash123",
        )
        session.add(doc)
        session.commit()

        # mock preview result
        _ = patch_external_services["mock_preview"]

        response = await client.post(
            app.url_path_for("v1_preview_kb_documents", kb_id=kb.id),
            headers=self.get_headers(api_key_value),
            json={
                "document_ids": [doc.id],
                "chunk_size": 50,
                "chunk_overlap": 0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert str(doc.id) in data
        assert data[str(doc.id)]["total_chunks"] == 2

    async def test_preview_with_upload(
        self,
        app: FastAPI,
        session: Session,
        client: AsyncClient,
        api_key_value,
        patch_external_services,
    ):
        """Preview route should work with existing DocumentUpload"""
        kb = KnowledgeBase(name="KB Test2", description="desc")
        session.add(kb)
        session.commit()

        upload = DocumentUpload(
            knowledge_base_id=kb.id,
            file_name="temp.txt",
            temp_path="tmp/temp.txt",
            file_size=5,
            content_type="text/plain",
            file_hash="h456",
            status="pending",
        )
        session.add(upload)
        session.commit()

        # mock preview result
        _ = patch_external_services["mock_preview"]

        response = await client.post(
            app.url_path_for("v1_preview_kb_documents", kb_id=kb.id),
            headers=self.get_headers(api_key_value),
            json={
                "document_ids": [upload.id],
                "chunk_size": 50,
                "chunk_overlap": 0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert str(upload.id) in data
        assert data[str(upload.id)]["total_chunks"] == 2

    async def test_preview_not_found(
        self,
        app: FastAPI,
        session: Session,
        client: AsyncClient,
        api_key_value: str,
    ):
        """Preview route should return 404 if document/upload not found"""
        kb = KnowledgeBase(name="KB Test3", description="desc")
        session.add(kb)
        session.commit()

        response = await client.post(
            app.url_path_for("v1_preview_kb_documents", kb_id=kb.id),
            headers=self.get_headers(api_key_value),
            json={
                "document_ids": [99999],
                "chunk_size": 50,
                "chunk_overlap": 0,
            },
        )

        assert response.status_code == 404
        assert "not found" in response.text

    async def test_preview_multiple_documents_and_uploads(
        self,
        app: FastAPI,
        session: Session,
        client: AsyncClient,
        api_key_value: str,
        patch_external_services,
    ):
        """
        Preview route should handle mix of Document and DocumentUpload in one
        request
        """
        kb = KnowledgeBase(name="KB Test4", description="desc")
        session.add(kb)
        session.commit()

        # add document
        doc = Document(
            knowledge_base_id=kb.id,
            file_name="doc_multi.txt",
            file_path=f"kb_{kb.id}/doc_multi.txt",
            file_size=20,
            content_type="text/plain",
            file_hash="hash789",
        )
        session.add(doc)
        session.commit()

        # add upload
        upload = DocumentUpload(
            knowledge_base_id=kb.id,
            file_name="upload_multi.txt",
            temp_path="tmp/upload_multi.txt",
            file_size=15,
            content_type="text/plain",
            file_hash="h987",
            status="pending",
        )
        session.add(upload)
        session.commit()

        # mock preview result
        mock_preview = patch_external_services["mock_preview"]
        # set mock to return different results depending on call order
        mock_preview.side_effect = [
            {
                "chunks": [{"content": "doc chunk", "metadata": {"page": 1}}],
                "total_chunks": 1,
            },
            {
                "chunks": [
                    {"content": "upload chunk", "metadata": {"page": 1}}
                ],
                "total_chunks": 1,
            },
        ]

        response = await client.post(
            app.url_path_for("v1_preview_kb_documents", kb_id=kb.id),
            headers=self.get_headers(api_key_value),
            json={
                "document_ids": [doc.id, upload.id],
                "chunk_size": 50,
                "chunk_overlap": 0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # both IDs must be present
        assert str(doc.id) in data
        assert str(upload.id) in data
        assert data[str(doc.id)]["total_chunks"] == 1
        assert data[str(upload.id)]["total_chunks"] == 1
        assert mock_preview.call_count == 2

    async def test_preview_empty_document_ids(
        self,
        app: FastAPI,
        client: AsyncClient,
        session: Session,
        api_key_value: str,
    ):
        """
        Preview route should return empty result if no document_ids provided
        """
        kb = KnowledgeBase(name="KB Test5", description="desc")
        session.add(kb)
        session.commit()

        response = await client.post(
            app.url_path_for("v1_preview_kb_documents", kb_id=kb.id),
            headers=self.get_headers(api_key_value),
            json={
                "document_ids": [],
                "chunk_size": 50,
                "chunk_overlap": 0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data == {}

    async def test_preview_duplicate_document_ids(
        self,
        app: FastAPI,
        session: Session,
        client: AsyncClient,
        api_key_value: str,
        patch_external_services,
    ):
        """Preview route should handle duplicate document_ids gracefully"""
        kb = KnowledgeBase(name="KB Test6", description="desc")
        session.add(kb)
        session.commit()

        doc = Document(
            knowledge_base_id=kb.id,
            file_name="dup.txt",
            file_path=f"kb_{kb.id}/dup.txt",
            file_size=5,
            content_type="text/plain",
            file_hash="hashdup",
        )
        session.add(doc)
        session.commit()

        # mock preview result
        mock_preview = patch_external_services["mock_preview"]

        response = await client.post(
            app.url_path_for("v1_preview_kb_documents", kb_id=kb.id),
            headers=self.get_headers(api_key_value),
            json={
                "document_ids": [doc.id, doc.id],
                "chunk_size": 50,
                "chunk_overlap": 0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # no duplicate keys in response
        assert list(data.keys()).count(str(doc.id)) == 1

        assert str(doc.id) in data
        assert data[str(doc.id)]["total_chunks"] == 2

        assert mock_preview.call_count == 2

    async def test_preview_duplicate_mixed_document_and_upload_ids(
        self,
        app: FastAPI,
        session: Session,
        client: AsyncClient,
        api_key_value: str,
        patch_external_services,
    ):
        """
        Preview route should handle duplicate mix of Document and
        DocumentUpload
        """
        kb = KnowledgeBase(name="KB Test7", description="desc")
        session.add(kb)
        session.commit()

        doc = Document(
            knowledge_base_id=kb.id,
            file_name="dup_mix_doc.txt",
            file_path=f"kb_{kb.id}/dup_mix_doc.txt",
            file_size=5,
            content_type="text/plain",
            file_hash="hashdoc",
        )
        session.add(doc)
        session.commit()

        upload = DocumentUpload(
            knowledge_base_id=kb.id,
            file_name="dup_mix_upload.txt",
            temp_path="tmp/dup_mix_upload.txt",
            file_size=7,
            content_type="text/plain",
            file_hash="hashupload",
            status="pending",
        )
        session.add(upload)
        session.commit()

        # mock preview result
        mock_preview = patch_external_services["mock_preview"]
        mock_preview.side_effect = [
            {
                "chunks": [{"content": "1 chunk", "metadata": {"page": 1}}],
                "total_chunks": 1,
            },
            {
                "chunks": [{"content": "2 chunk", "metadata": {"page": 1}}],
                "total_chunks": 1,
            },
            {
                "chunks": [{"content": "3 chunk", "metadata": {"page": 1}}],
                "total_chunks": 1,
            },
            {
                "chunks": [{"content": "4 chunk", "metadata": {"page": 1}}],
                "total_chunks": 1,
            },
        ]

        response = await client.post(
            app.url_path_for("v1_preview_kb_documents", kb_id=kb.id),
            headers=self.get_headers(api_key_value),
            json={
                "document_ids": [doc.id, upload.id, doc.id, upload.id],
                "chunk_size": 50,
                "chunk_overlap": 0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # No duplicate keys in response
        assert list(data.keys()).count(str(doc.id)) == 1
        assert list(data.keys()).count(str(upload.id)) == 1

        assert str(doc.id) in data
        assert str(upload.id) in data
        assert data[str(doc.id)]["total_chunks"] == 1
        assert data[str(upload.id)]["total_chunks"] == 1

        assert mock_preview.call_count == 4
