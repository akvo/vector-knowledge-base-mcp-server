import pytest

from fastapi import HTTPException
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from app.models.knowledge import (
    KnowledgeBase,
    DocumentUpload,
    ProcessingTask,
)
from app.services.document_service import DocumentService, Document
from app.services.document_processor import PreviewResult
from app.core.config import settings


@pytest.mark.unit
@pytest.mark.asyncio
class TestDocumentService:
    async def test_upload_documents_success(
        self, session, patch_external_services, mocker
    ):
        kb = KnowledgeBase(name="KB Upload", description="testing upload")
        session.add(kb)
        session.commit()

        mock_minio = patch_external_services["mock_minio"]
        mock_put = mock_minio.put_object

        # Fake upload file
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

        # ensure MinIO upload called
        mock_put.assert_called_once()

    async def test_upload_documents_kb_not_found(self, session):
        service = DocumentService(999, session)
        with pytest.raises(HTTPException) as exc:
            await service.upload_documents([])
        assert exc.value.status_code == 404

    async def test_upload_documents_minio_failure(
        self, session, patch_external_services
    ):
        kb = KnowledgeBase(name="KB Upload Fail", description="testing fail")
        session.add(kb)
        session.commit()

        mock_minio = patch_external_services["mock_minio"]
        mock_minio.put_object.side_effect = Exception("MinIO failed")

        class DummyFile:
            filename = "bad.txt"
            content_type = "text/plain"
            file = MagicMock()

            async def read(self):
                return b"broken"

            async def seek(self, pos):
                return None

        service = DocumentService(kb.id, session)

        with pytest.raises(HTTPException) as exc:
            await service.upload_documents([DummyFile()])

        assert exc.value.status_code == 500

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

    @patch("app.services.document_service.process_document_task.delay")
    async def test_process_documents_creates_tasks(
        self, mock_delay, session, patch_external_services, mock_celery
    ):
        mock_delay.return_value.id = "fake-celery-task-id-321"
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

        upload_results = [
            {"upload_id": upload.id, "file_name": upload.file_name}
        ]
        result = await service.process_documents(upload_results)

        assert "tasks" in result
        assert result["tasks"][0]["upload_id"] == upload.id

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

    async def test_cleanup_temp_files_removes_minio_file(
        self, session, patch_external_services, mocker
    ):
        kb = KnowledgeBase(name="KB Clean", description="clean test")
        session.add(kb)
        session.commit()

        mock_minio = patch_external_services["mock_minio"]

        # Make upload older than 24h
        old_upload = DocumentUpload(
            knowledge_base_id=kb.id,
            file_name="old.txt",
            file_hash="hash",
            file_size=10,
            content_type="text/plain",
            temp_path="kb_1/temp/old.txt",
        )
        old_upload.created_at = datetime.utcnow() - timedelta(days=2)
        session.add(old_upload)
        session.commit()

        service = DocumentService(kb.id, session)

        result = await service.cleanup_temp_files()

        # MinIO delete called
        mock_minio.remove_object.assert_called_once_with(
            settings.minio_bucket_name, "kb_1/temp/old.txt"
        )

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

    @patch("app.services.document_service.cleanup_doc_task.delay")
    async def test_delete_document_success(
        self, mock_delay, session, patch_external_services, mocker, mock_celery
    ):
        # Return a real string as Celery task ID
        mock_delay.return_value.id = "fake-celery-task-id-911"

        kb = KnowledgeBase(name="KB Del", description="delete test")
        session.add(kb)
        session.commit()

        # Prepare document
        doc = Document(
            knowledge_base_id=kb.id,
            file_name="doc.txt",
            file_hash="h",
            file_size=10,
            content_type="text/plain",
            file_path="kb_1/documents/doc.txt",
        )
        session.add(doc)
        session.commit()

        service = DocumentService(kb.id, session)

        result = await service.delete_document(doc.id, user=None)

        assert result["success"]
        assert result["document_id"] == doc.id
        assert result["celery_task_id"] is not None

    @patch("app.services.document_service.cleanup_doc_task.delay")
    async def test_delete_document_uses_file_hash(
        self, mock_delay, session, patch_external_services, mocker, mock_celery
    ):
        # Return a real string as Celery task ID
        mock_delay.return_value.id = "fake-celery-task-id-912"

        kb = KnowledgeBase(name="KB Delete Hash", description="hash test")
        session.add(kb)
        session.commit()

        # Prepare document
        doc = Document(
            knowledge_base_id=kb.id,
            file_name="doc.txt",
            file_hash="FILEHASH123",
            file_size=10,
            content_type="text/plain",
            file_path="kb_1/documents/doc.txt",
        )
        session.add(doc)
        session.commit()

        # Matching upload (same file_hash)
        upload = DocumentUpload(
            knowledge_base_id=kb.id,
            file_name="doc.txt",
            file_hash="FILEHASH123",
            file_size=10,
            content_type="text/plain",
            temp_path="kb_1/temp/doc.txt",
        )
        session.add(upload)
        session.commit()

        service = DocumentService(kb.id, session)

        # Run delete
        result = await service.delete_document(doc.id)

        assert result["success"] is True
        assert result["deleted_from"] == "documents"

    @patch("app.services.document_service.cleanup_doc_task.delay")
    async def test_delete_upload_when_document_not_found(
        self, mock_delay, session, patch_external_services, mock_celery
    ):
        # Return a real string as Celery task ID
        mock_delay.return_value.id = "fake-celery-task-id-913"

        kb = KnowledgeBase(name="KB Del Upload", description="delete upload")
        session.add(kb)
        session.commit()

        # Only Upload exists
        upload = DocumentUpload(
            knowledge_base_id=kb.id,
            file_name="upload.txt",
            file_hash="XYZ",
            file_size=10,
            content_type="text/plain",
            temp_path="kb_1/temp/upload.txt",
        )
        session.add(upload)
        session.commit()

        service = DocumentService(kb.id, session)

        result = await service.delete_document(upload.id)

        assert result["deleted_from"] == "document_uploads"
        assert result["success"] is True

    async def test_get_presigned_file_info_success(self, session):
        kb = KnowledgeBase(name="KB Info", description="info test")
        session.add(kb)
        session.commit()

        doc = Document(
            knowledge_base_id=kb.id,
            file_name="file.pdf",
            file_hash="h",
            file_size=10,
            content_type="application/pdf",
            file_path=f"kb_{kb.id}/documents/file.pdf",
        )
        session.add(doc)
        session.commit()

        service = DocumentService(kb.id, session)

        result = await service.get_presigned_file_info(doc.id)

        # URL format: {minio_server_url}/{bucket}/{file_path}
        expected_prefix = (
            f"{settings.minio_server_url}/"
            f"{settings.minio_bucket_name}/"
            f"kb_{kb.id}/documents/file.pdf"
        )
        assert result["file_url"] == expected_prefix
        assert result["file_name"] == "file.pdf"
        assert result["document_id"] == doc.id
