import io
import pytest

from unittest.mock import MagicMock
from fastapi import UploadFile

from app.services import document_processor
from app.models.knowledge import (
    ProcessingTask,
    DocumentUpload,
    KnowledgeBase,
    Document,
)


@pytest.mark.asyncio
class TestDocumentProcessor:
    async def test_generate_chunk_id_consistency(self):
        h1, cid1 = document_processor.generate_chunk_id(
            kb_id=1,
            file_name="a.txt",
            chunk_content="hello",
            chunk_metadata={"p": 1},
        )
        h2, cid2 = document_processor.generate_chunk_id(
            kb_id=1,
            file_name="a.txt",
            chunk_content="hello",
            chunk_metadata={"p": 1},
        )
        assert h1 == h2
        assert cid1 == cid2

    async def test_upload_document_success(self, patch_external_services):
        mock_minio = patch_external_services["mock_minio"]
        file_content = b"Hello world"
        upload_file = UploadFile(
            filename="test.txt", file=io.BytesIO(file_content)
        )

        result = await document_processor.upload_document(upload_file, kb_id=1)

        assert result.file_name == "test.txt"
        assert result.file_size == len(file_content)
        assert result.content_type == "text/plain"
        mock_minio.put_object.assert_called_once()

    async def test_upload_document_failure(self, patch_external_services):
        mock_minio = patch_external_services["mock_minio"]
        mock_minio.put_object.side_effect = Exception("upload failed")

        upload_file = UploadFile(filename="fail.txt", file=io.BytesIO(b"abc"))

        with pytest.raises(Exception, match="upload failed"):
            await document_processor.upload_document(upload_file, kb_id=1)

    async def test_preview_document_txt(self, patch_external_services):
        # Call preview_document async mock
        _ = patch_external_services["mock_preview"]
        result = await document_processor.preview_document(
            "dummy.txt", chunk_size=10, chunk_overlap=0
        )
        assert result.total_chunks == 2
        assert all(isinstance(c.content, str) for c in result.chunks)

    async def test_process_document_add_and_delete(
        self, patch_external_services, session
    ):
        _ = patch_external_services["mock_preview"]
        mock_vs = patch_external_services["mock_vector_store"]
        mock_manager = MagicMock()
        mock_manager.list_chunks.return_value = set()
        mock_manager.get_deleted_chunks.return_value = ["oldchunk"]

        # Patch ChunkRecord
        document_processor.ChunkRecord = MagicMock(return_value=mock_manager)
        document_processor.ChromaVectorStore = MagicMock(return_value=mock_vs)
        document_processor.EmbeddingsFactory.create = (
            lambda: patch_external_services["mock_embeddings"]
        )

        kb = KnowledgeBase(name="KB1", description="desc")
        session.add(kb)
        session.commit()

        doc = Document(
            knowledge_base_id=kb.id,
            file_name="doc.txt",
            file_path="/tmp/doc.txt",
            file_size=10,
            content_type="text/plain",
            file_hash="h123",
        )
        session.add(doc)
        session.commit()

        await document_processor.process_document(
            file_path="doc.txt",
            file_name="doc.txt",
            kb_id=kb.id,
            document_id=doc.id,
        )

        assert mock_manager.add_chunks.called
        assert mock_vs.add_documents.called
        assert mock_manager.delete_chunks.called
        assert mock_vs.delete.called

    async def test_process_document_background_task_not_found(
        self, patch_external_services, session
    ):
        await document_processor.process_document_background(
            temp_path="tmp/test.txt",
            file_name="test.txt",
            file_size=10,
            kb_id=1,
            task_id=999,
            db=session,
        )

    async def test_process_document_background_success(
        self, patch_external_services, session, tmp_path
    ):
        kb = KnowledgeBase(name="KB2", description="desc")
        session.add(kb)
        session.commit()

        upload = DocumentUpload(
            file_name="test.txt",
            temp_path="tmp/test.txt",
            file_size=5,
            content_type="text/plain",
            file_hash="h123",
            knowledge_base_id=kb.id,
            status="pending",
        )
        session.add(upload)
        session.commit()

        task = ProcessingTask(
            knowledge_base_id=kb.id,
            document_upload_id=upload.id,
            status="pending",
        )
        session.add(task)
        session.commit()

        # background processing
        await document_processor.process_document_background(
            temp_path="tmp/test.txt",
            file_name="test.txt",
            kb_id=kb.id,
            task_id=task.id,
            db=session,
        )

        session.refresh(task)
        session.refresh(upload)

        assert task.status == "completed"
        assert task.document_id is not None
        assert upload.status == "completed"
        patch_external_services[
            "mock_vector_store"
        ].add_documents.assert_called()
