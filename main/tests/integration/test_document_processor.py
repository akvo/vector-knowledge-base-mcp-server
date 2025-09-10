import io
import pytest

from unittest.mock import patch, MagicMock
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

    @patch("app.services.document_processor.get_minio_client")
    async def test_upload_document_success(self, mock_minio):
        mock_client = MagicMock()
        mock_minio.return_value = mock_client

        file_content = b"Hello world"
        upload_file = UploadFile(
            filename="test.txt", file=io.BytesIO(file_content)
        )

        result = await document_processor.upload_document(upload_file, kb_id=1)

        assert result.file_name == "test.txt"
        assert result.file_size == len(file_content)
        assert result.content_type == "text/plain"
        mock_client.put_object.assert_called_once()

    @patch("app.services.document_processor.get_minio_client")
    async def test_upload_document_failure(self, mock_minio):
        mock_client = MagicMock()
        mock_client.put_object.side_effect = Exception("upload failed")
        mock_minio.return_value = mock_client

        upload_file = UploadFile(filename="fail.txt", file=io.BytesIO(b"abc"))

        with pytest.raises(Exception, match="upload failed"):
            await document_processor.upload_document(upload_file, kb_id=1)

    @patch("app.services.document_processor.get_minio_client")
    async def test_preview_document_txt(self, mock_minio, tmp_path):
        # dummy file
        file_path = "kb_1/test.txt"
        local_file = tmp_path / "test.txt"
        local_file.write_text("Hello world. This is a test document.")

        mock_client = MagicMock()
        mock_client.fget_object.side_effect = (
            lambda bucket_name, object_name, file_path: local_file.rename(
                file_path
            )
        )
        mock_minio.return_value = mock_client

        result = await document_processor.preview_document(
            file_path, chunk_size=10, chunk_overlap=0
        )

        assert result.total_chunks > 0
        assert all(isinstance(c.content, str) for c in result.chunks)

    @patch("app.services.document_processor.EmbeddingsFactory")
    @patch("app.services.document_processor.ChromaVectorStore")
    @patch("app.services.document_processor.ChunkRecord")
    @patch("app.services.document_processor.preview_document")
    async def test_process_document_add_and_delete(
        self,
        mock_preview,
        mock_chunk_record,
        mock_chroma,
        mock_embeddings,
        session,
    ):
        # arrange DB
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

        # mock preview result
        mock_preview.return_value = document_processor.PreviewResult(
            chunks=[
                document_processor.TextChunk(
                    content="hello", metadata={"page": 1}
                ),
                document_processor.TextChunk(
                    content="world", metadata={"page": 2}
                ),
            ],
            total_chunks=2,
        )

        # mock chunk record
        mock_manager = MagicMock()
        mock_manager.list_chunks.return_value = set()
        mock_manager.get_deleted_chunks.return_value = ["oldchunk"]
        mock_chunk_record.return_value = mock_manager

        # mock vector store
        mock_vs = MagicMock()
        mock_chroma.return_value = mock_vs

        # act
        await document_processor.process_document(
            file_path="doc.txt",
            file_name="doc.txt",
            kb_id=kb.id,
            document_id=doc.id,
        )

        # assert new chunks
        assert mock_manager.add_chunks.called
        assert mock_vs.add_documents.called
        assert mock_manager.delete_chunks.called
        assert mock_vs.delete.called

    @patch("app.services.document_processor.get_minio_client")
    async def test_process_document_background_task_not_found(
        self, mock_minio, session
    ):
        await document_processor.process_document_background(
            temp_path="tmp/test.txt",
            file_name="test.txt",
            kb_id=1,
            task_id=999,
            db=session,
        )

    @patch("app.services.document_processor.get_minio_client")
    @patch("app.services.document_processor.EmbeddingsFactory")
    @patch("app.services.document_processor.ChromaVectorStore")
    async def test_process_document_background_success(
        self, mock_chroma, mock_embeddings, mock_minio, session, tmp_path
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

        # minio dummy file
        dummy_file = tmp_path / "test.txt"
        dummy_file.write_text("Hello world again")

        mock_client = MagicMock()

        def mock_fget_object(*args, **kwargs):
            dest = kwargs.get("file_path") or args[2]
            dummy_file.rename(dest)

        mock_client.fget_object.side_effect = mock_fget_object
        mock_client.copy_object.return_value = None
        mock_client.remove_object.return_value = None
        mock_minio.return_value = mock_client

        # mock embeddings + vector store
        mock_embeddings.create.return_value = MagicMock()
        mock_vs = MagicMock()
        mock_chroma.return_value = mock_vs

        # act
        await document_processor.process_document_background(
            temp_path="tmp/test.txt",
            file_name="test.txt",
            kb_id=kb.id,
            task_id=task.id,
            db=session,
        )

        session.refresh(task)
        assert task.status == "completed"
        assert task.document_id is not None
        assert upload.status == "completed"
        assert mock_vs.add_documents.called
