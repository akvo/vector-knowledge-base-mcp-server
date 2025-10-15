import pytest

from fastapi import HTTPException
from unittest.mock import MagicMock
from starlette.background import BackgroundTasks

from app.models.knowledge import (
    KnowledgeBase,
    DocumentUpload,
    ProcessingTask,
)
from app.services.document_service import DocumentService
from app.services.document_processor import PreviewResult


@pytest.mark.unit
@pytest.mark.asyncio
class TestDocumentService:
    async def test_upload_documents_success(
        self, session, patch_external_services, tmp_path
    ):
        kb = KnowledgeBase(name="KB Upload", description="testing upload")
        session.add(kb)
        session.commit()

        # fake upload file
        class DummyFile:
            def __init__(self, name, content=b"hello"):
                self.filename = name
                self.content_type = "text/plain"
                self.file = MagicMock()
                self._content = content

            async def read(self):
                return self._content

            async def seek(self, pos):
                return None

        file = DummyFile("test.txt", b"hello")
        service = DocumentService(kb.id, session)

        results = await service.upload_documents([file])
        assert results[0]["status"] == "pending"
        assert results[0]["file_name"] == "test.txt"
        assert not results[0]["skip_processing"]

    async def test_upload_documents_kb_not_found(self, session):
        service = DocumentService(999, session)
        with pytest.raises(HTTPException) as exc:
            await service.upload_documents([])
        assert exc.value.status_code == 404

    async def test_preview_documents_success(
        self, session, patch_external_services
    ):
        kb = KnowledgeBase(name="KB Preview", description="preview test")
        session.add(kb)
        session.commit()

        upload = DocumentUpload(
            knowledge_base_id=kb.id,
            file_name="doc.txt",
            file_hash="hash",
            file_size=10,
            content_type="text/plain",
            temp_path="kb_1/temp/doc.txt",
        )
        session.add(upload)
        session.commit()

        service = DocumentService(kb.id, session)

        class DummyReq:
            document_ids = [upload.id]
            chunk_size = 100
            chunk_overlap = 0

        result = await service.preview_documents(DummyReq())
        assert upload.id in result
        preview = result[upload.id]
        assert isinstance(preview, PreviewResult)
        assert preview.total_chunks == 2  # comes from patch_external_services

    async def test_process_documents_creates_tasks(
        self, session, patch_external_services
    ):
        kb = KnowledgeBase(name="KB Proc", description="proc test")
        session.add(kb)
        session.commit()

        upload = DocumentUpload(
            knowledge_base_id=kb.id,
            file_name="doc.txt",
            file_hash="hash",
            file_size=10,
            content_type="text/plain",
            temp_path="kb_1/temp/doc.txt",
        )
        session.add(upload)
        session.commit()

        service = DocumentService(kb.id, session)

        background = BackgroundTasks()
        upload_results = [
            {"upload_id": upload.id, "file_name": upload.file_name}
        ]
        result = await service.process_documents(upload_results, background)

        assert "tasks" in result
        assert result["tasks"][0]["upload_id"] == upload.id
        # Background task should be scheduled
        assert background.tasks

    async def test_cleanup_temp_files(self, session, patch_external_services):
        kb = KnowledgeBase(name="KB Clean", description="clean test")
        session.add(kb)
        session.commit()

        # make an expired upload
        upload = DocumentUpload(
            knowledge_base_id=kb.id,
            file_name="old.txt",
            file_hash="hash",
            file_size=10,
            content_type="text/plain",
            temp_path="kb_1/temp/old.txt",
        )
        session.add(upload)
        session.commit()

        service = DocumentService(kb.id, session)
        result = await service.cleanup_temp_files()
        assert "Cleaned" in result["message"]

    async def test_get_processing_tasks(self, session):
        kb = KnowledgeBase(name="KB Tasks", description="tasks test")
        session.add(kb)
        session.commit()

        upload = DocumentUpload(
            knowledge_base_id=kb.id,
            file_name="doc.txt",
            file_hash="hash",
            file_size=10,
            content_type="text/plain",
            temp_path="kb_1/temp/doc.txt",
        )
        session.add(upload)
        session.commit()

        task = ProcessingTask(
            document_upload_id=upload.id,
            knowledge_base_id=kb.id,
            status="pending",
        )
        session.add(task)
        session.commit()

        service = DocumentService(kb.id, session)
        result = await service.get_processing_tasks(str(task.id))
        assert task.id in result
        assert result[task.id]["status"] == "pending"

    async def test_get_document_not_found(self, session):
        kb = KnowledgeBase(name="KB Doc", description="doc test")
        session.add(kb)
        session.commit()

        service = DocumentService(kb.id, session)
        with pytest.raises(HTTPException) as exc:
            await service.get_document(999)
        assert exc.value.status_code == 404

    async def test_search_success(self, session, patch_external_services):
        kb = KnowledgeBase(name="KB Search", description="search test")
        session.add(kb)
        session.commit()

        service = DocumentService(kb.id, session)
        results = service.search("hello", top_k=2)
        assert isinstance(results, list)
        assert "content" in results[0]
        assert "score" in results[0]

    async def test_search_failure(self, session, patch_external_services):
        kb = KnowledgeBase(
            name="KB SearchFail", description="search fail test"
        )
        session.add(kb)
        session.commit()

        # break vector_store
        patch_external_services[
            "mock_vector_store"
        ].similarity_search_with_score.side_effect = Exception("search down")

        service = DocumentService(kb.id, session)
        with pytest.raises(HTTPException) as exc:
            service.search("hello")
        assert exc.value.status_code == 500

    async def test_get_documents_success(self, session):
        """✅ Should return all documents with content_type for a KB"""
        kb = KnowledgeBase(name="KB Docs", description="list documents")
        session.add(kb)
        session.commit()

        # Create some documents
        docs = [
            DocumentUpload(
                knowledge_base_id=kb.id,
                file_name="file1.txt",
                file_hash="hash1",
                file_size=10,
                content_type="text/plain",
                temp_path=f"kb_{kb.id}/temp/file1.txt",
                status="processed",
            ),
            DocumentUpload(
                knowledge_base_id=kb.id,
                file_name="file2.txt",
                file_hash="hash2",
                file_size=20,
                content_type="application/pdf",
                temp_path=f"kb_{kb.id}/temp/file2.txt",
                status="pending",
            ),
        ]
        session.add_all(docs)
        session.commit()

        service = DocumentService(kb.id, session)
        result = service.get_documents_upload()

        assert len(result) == 2
        for doc_data, doc in zip(result, docs):
            assert doc_data["id"] == doc.id
            assert doc_data["file_name"] == doc.file_name
            assert doc_data["status"] == doc.status
            assert doc_data["content_type"] == doc.content_type
