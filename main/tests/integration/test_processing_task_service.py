from app.models import KnowledgeBase, DocumentUpload, ProcessingTask
from app.services.processing_task_service import (
    ProcessingTaskService,
    JobTypeEnum,
)


class TestProcessingTaskService:
    def _create_kb_and_upload(self, session):
        """Helper to insert a KB and a DocumentUpload into the test DB."""
        kb = KnowledgeBase(name="Test KB", description="KB for testing")
        session.add(kb)
        session.commit()
        session.refresh(kb)

        upload = DocumentUpload(
            knowledge_base_id=kb.id,
            file_name="test.txt",
            file_hash="hash123",
            file_size=123,
            content_type="text/plain",
            temp_path="/tmp/test.txt",
        )
        session.add(upload)
        session.commit()
        session.refresh(upload)

        return kb, upload

    def test_create_task(self, session):
        """Should create a new ProcessingTask with pending status"""
        kb, upload = self._create_kb_and_upload(session)
        service = ProcessingTaskService(session)
        task = service.create_task(
            kb_id=kb.id, upload_id=upload.id, job_type=JobTypeEnum.process_doc
        )

        assert task.id is not None
        assert task.knowledge_base_id == kb.id
        assert task.document_upload_id == upload.id
        assert task.status == "pending"
        assert task.job_type == JobTypeEnum.process_doc.value

        db_task = session.query(ProcessingTask).get(task.id)
        assert db_task is not None

    def test_update_status(self, session):
        """Should update the task status and optional error message"""
        kb, upload = self._create_kb_and_upload(session)
        service = ProcessingTaskService(session)
        task = service.create_task(
            kb_id=kb.id, upload_id=upload.id, job_type=JobTypeEnum.process_doc
        )

        updated = service.update_status(task.id, "processing")
        assert updated.status == "processing"

        failed = service.update_status(
            task.id, "failed", "Something went wrong"
        )
        assert failed.status == "failed"
        assert failed.error_message == "Something went wrong"

    def test_get_task(self, session):
        """Should retrieve a specific ProcessingTask by id"""
        kb, upload = self._create_kb_and_upload(session)
        service = ProcessingTaskService(session)
        created = service.create_task(
            kb_id=kb.id, upload_id=upload.id, job_type=JobTypeEnum.process_doc
        )

        found = service.get_task(created.id)
        assert found is not None
        assert found.id == created.id
        assert found.status == "pending"

    def test_mark_status_helpers(self, session):
        """
        Should update status via helper methods
        (mark_processing, mark_completed, mark_failed)
        """
        kb, upload = self._create_kb_and_upload(session)
        service = ProcessingTaskService(session)
        created = service.create_task(
            kb_id=kb.id, upload_id=upload.id, job_type=JobTypeEnum.process_doc
        )

        processing = service.mark_processing(created.id)
        assert processing.status == "processing"

        completed = service.mark_completed(created.id)
        assert completed.status == "completed"

        failed = service.mark_failed(created.id, "fail reason")
        assert failed.status == "failed"
        assert failed.error_message == "fail reason"

    def test_list_tasks(self, session):
        """Should list tasks filtered by knowledge base id"""
        kb1, upload1 = self._create_kb_and_upload(session)
        kb2, upload2 = self._create_kb_and_upload(session)
        service = ProcessingTaskService(session)

        service.create_task(
            kb_id=kb1.id,
            upload_id=upload1.id,
            job_type=JobTypeEnum.process_doc,
        )
        service.create_task(
            kb_id=kb1.id,
            upload_id=upload1.id,
            job_type=JobTypeEnum.process_doc,
        )
        service.create_task(
            kb_id=kb2.id,
            upload_id=upload2.id,
            job_type=JobTypeEnum.process_doc,
        )

        tasks_kb1 = service.list_tasks(kb1.id)
        tasks_kb2 = service.list_tasks(kb2.id)

        assert len(tasks_kb1) == 2
        assert all(t.knowledge_base_id == kb1.id for t in tasks_kb1)
        assert len(tasks_kb2) == 1
        assert tasks_kb2[0].knowledge_base_id == kb2.id

    def test_update_status_invalid_id_returns_none(self, session):
        """Should safely handle updating a non-existing ProcessingTask"""
        service = ProcessingTaskService(session)

        # Try updating a task that doesn’t exist
        result = service.update_status(9999, "processing")
        assert result is None, "Expected None for non-existent task id"

    def test_get_task_invalid_id_returns_none(self, session):
        """Should return None when trying to get a non-existent task"""
        service = ProcessingTaskService(session)

        result = service.get_task(9999)
        assert result is None, "Expected None for non-existent task id"
