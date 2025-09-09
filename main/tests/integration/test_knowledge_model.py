import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.knowledge import (
    KnowledgeBase,
    Document,
    DocumentUpload,
    DocumentChunk,
    ProcessingTask,
)


@pytest.mark.usefixtures("session")
class TestKnowledgeModels:
    def test_knowledge_base_timestamps(self, session: Session):
        """KnowledgeBase should auto-populate created_at and updated_at"""
        kb = KnowledgeBase(name="Test KB", description="Integration test KB")
        session.add(kb)
        session.commit()
        session.refresh(kb)

        assert kb.name == "Test KB"
        assert kb.description == "Integration test KB"
        assert isinstance(kb.created_at, datetime)
        assert isinstance(kb.updated_at, datetime)

    def test_document_unique_constraint(self, session: Session):
        """Document.file_name must be unique within the same KB"""
        kb = KnowledgeBase(name="KB Unique")
        session.add(kb)
        session.commit()

        doc1 = Document(
            file_path="/tmp/a.pdf",
            file_name="a.pdf",
            file_size=123,
            content_type="application/pdf",
            knowledge_base_id=kb.id,
        )
        session.add(doc1)
        session.commit()

        # Duplicate file_name should fail within same KB
        doc2 = Document(
            file_path="/tmp/b.pdf",
            file_name="a.pdf",
            file_size=456,
            content_type="application/pdf",
            knowledge_base_id=kb.id,
        )
        session.add(doc2)
        with pytest.raises(IntegrityError):
            session.commit()
            session.rollback()

    def test_document_chunk_relationship(self, session: Session):
        """DocumentChunk should have proper relationships to KB and Document"""
        kb = KnowledgeBase(name="KB Chunk")
        session.add(kb)
        session.commit()

        doc = Document(
            file_path="/tmp/doc.pdf",
            file_name="doc.pdf",
            file_size=100,
            content_type="application/pdf",
            knowledge_base_id=kb.id,
        )
        session.add(doc)
        session.commit()

        chunk = DocumentChunk(
            id="chunk1",
            kb_id=kb.id,
            document_id=doc.id,
            file_name="doc.pdf",
            hash="hash123",
        )
        session.add(chunk)
        session.commit()
        session.refresh(chunk)

        assert chunk.knowledge_base.id == kb.id
        assert chunk.document.id == doc.id

    def test_processing_task_defaults(self, session: Session):
        """ProcessingTask should set default timestamps and status"""
        kb = KnowledgeBase(name="KB Task")
        session.add(kb)
        session.commit()

        task = ProcessingTask(knowledge_base_id=kb.id, status="pending")
        session.add(task)
        session.commit()
        session.refresh(task)

        assert task.created_at is not None
        assert task.updated_at is not None
        assert task.status == "pending"

    def test_document_upload_cascade(self, session: Session):
        """Deleting KB should cascade delete its DocumentUpload"""
        kb = KnowledgeBase(name="KB Upload")
        session.add(kb)
        session.commit()

        upload = DocumentUpload(
            knowledge_base_id=kb.id,
            file_name="upload.pdf",
            file_hash="hash123",
            file_size=10,
            content_type="application/pdf",
            temp_path="/tmp/upload.pdf",
        )
        session.add(upload)
        session.commit()
        session.refresh(upload)

        # deleting KB should cascade to upload
        session.delete(kb)
        session.commit()

        remaining = (
            session.query(DocumentUpload).filter_by(id=upload.id).first()
        )
        assert remaining is None
