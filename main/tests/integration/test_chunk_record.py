import pytest
from app.services.chunk_record import ChunkRecord
from app.models.knowledge import KnowledgeBase, Document, DocumentChunk


@pytest.mark.asyncio
class TestChunkRecord:
    def setup_method(self, method):
        self.kb_id = None
        self.chunk_record = None

    def _create_kb_and_doc(self, session):
        """Helper dummy KB and Document"""
        kb = KnowledgeBase(name="KB Test", description="desc")
        session.add(kb)
        session.commit()

        doc = Document(
            knowledge_base_id=kb.id,
            file_name="file1.txt",
            file_path="/tmp/file1.txt",
            file_size=123,
            content_type="text/plain",
            file_hash="doc-hash-1",
        )
        session.add(doc)
        session.commit()

        self.kb_id = kb.id
        self.chunk_record = ChunkRecord(self.kb_id)
        return kb, doc

    def test_add_and_list_chunks(self, session):
        kb, doc = self._create_kb_and_doc(session)

        chunks = [
            {
                "id": "c1",
                "kb_id": kb.id,
                "document_id": doc.id,
                "file_name": doc.file_name,
                "metadata": {"page": 1},
                "hash": "h1",
            },
            {
                "id": "c2",
                "kb_id": kb.id,
                "document_id": doc.id,
                "file_name": doc.file_name,
                "metadata": {"page": 2},
                "hash": "h2",
            },
        ]

        self.chunk_record.add_chunks(chunks)

        stored = (
            session.query(DocumentChunk)
            .filter(DocumentChunk.kb_id == kb.id)
            .all()
        )
        assert len(stored) == 2

        hashes = self.chunk_record.list_chunks()
        assert hashes == {"h1", "h2"}

        hashes_for_file = self.chunk_record.list_chunks("file1.txt")
        assert hashes_for_file == {"h1", "h2"}

    def test_delete_chunks(self, session):
        kb, doc = self._create_kb_and_doc(session)

        chunk = DocumentChunk(
            id="c3",
            kb_id=kb.id,
            document_id=doc.id,
            file_name="file2.txt",
            chunk_metadata={},
            hash="h3",
        )
        session.add(chunk)
        session.commit()

        assert (
            session.query(DocumentChunk)
            .filter_by(id=chunk.id, kb_id=kb.id)
            .first()
            is not None
        )

        self.chunk_record.delete_chunks([chunk.id])

        assert (
            session.query(DocumentChunk)
            .filter_by(id=chunk.id, kb_id=kb.id)
            .first()
            is None
        )

    def test_get_deleted_chunks(self, session):
        kb, doc = self._create_kb_and_doc(session)

        chunk1 = DocumentChunk(
            id="c4",
            kb_id=kb.id,
            document_id=doc.id,
            file_name="file3.txt",
            chunk_metadata={},
            hash="h4",
        )
        chunk2 = DocumentChunk(
            id="c5",
            kb_id=kb.id,
            document_id=doc.id,
            file_name="file3.txt",
            chunk_metadata={},
            hash="h5",
        )
        session.add_all([chunk1, chunk2])
        session.commit()

        deleted_ids = self.chunk_record.get_deleted_chunks(
            current_hashes={"h4"}, file_name="file3.txt"
        )

        assert chunk2.id in deleted_ids
        assert chunk1.id not in deleted_ids

    # -----------------
    # Edge Cases
    # -----------------
    def test_add_chunks_empty_list(self, session):
        kb, doc = self._create_kb_and_doc(session)
        self.chunk_record.add_chunks([])

        stored = (
            session.query(DocumentChunk)
            .filter(DocumentChunk.kb_id == kb.id)
            .all()
        )
        assert len(stored) == 0

    def test_delete_chunks_empty_list(self, session):
        kb, doc = self._create_kb_and_doc(session)

        chunk = DocumentChunk(
            id="c6",
            kb_id=kb.id,
            document_id=doc.id,
            file_name="fileX.txt",
            chunk_metadata={},
            hash="hx",
        )
        session.add(chunk)
        session.commit()

        self.chunk_record.delete_chunks([])

        # data exist
        stored = (
            session.query(DocumentChunk)
            .filter_by(id=chunk.id, kb_id=kb.id)
            .first()
        )
        assert stored is not None

    def test_get_deleted_chunks_with_empty_current_hashes(self, session):
        kb, doc = self._create_kb_and_doc(session)

        chunk1 = DocumentChunk(
            id="c7",
            kb_id=kb.id,
            document_id=doc.id,
            file_name="fileY.txt",
            chunk_metadata={},
            hash="hy1",
        )
        chunk2 = DocumentChunk(
            id="c8",
            kb_id=kb.id,
            document_id=doc.id,
            file_name="fileY.txt",
            chunk_metadata={},
            hash="hy2",
        )
        session.add_all([chunk1, chunk2])
        session.commit()

        deleted_ids = self.chunk_record.get_deleted_chunks(
            current_hashes=set(), file_name="fileY.txt"
        )

        assert chunk1.id in deleted_ids
        assert chunk2.id in deleted_ids
