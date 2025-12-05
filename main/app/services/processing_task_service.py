import logging
import enum

from sqlalchemy.orm import Session
from app.models import ProcessingTask
from datetime import datetime

logger = logging.getLogger(__name__)


class JobTypeEnum(str, enum.Enum):
    delete_kb = "delete_kb"
    process_doc = "process_doc"


class ProcessingTaskService:
    """
    Service layer for CRUD operations and state transitions
    of processing tasks.
    """

    def __init__(self, db: Session):
        self.db = db

    # -------------------------------
    # CREATE
    # -------------------------------
    def create_task(
        self,
        kb_id: int,
        job_type: JobTypeEnum,
        upload_id: int = None,
        celery_task_id: str = None,
    ) -> ProcessingTask:
        task = ProcessingTask(
            knowledge_base_id=kb_id,
            document_upload_id=upload_id,
            celery_task_id=celery_task_id,
            status="pending",
            job_type=job_type.value,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    # -------------------------------
    # UPDATE STATUS
    # -------------------------------
    def update_status(
        self,
        task_id: int,
        status: str = "pending",
        error_message: str = None,
        celery_task_id: str = None,
    ):
        task = self.db.query(ProcessingTask).get(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found for update_status")
            return None
        task.status = status
        if error_message:
            task.error_message = error_message
        if celery_task_id:
            task.celery_task_id = celery_task_id
        task.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(task)
        return task

    # -------------------------------
    # RETRIEVE
    # -------------------------------
    def get_task(self, task_id: int) -> ProcessingTask:
        return self.db.query(ProcessingTask).get(task_id)

    def list_tasks(self, kb_id: int):
        return (
            self.db.query(ProcessingTask)
            .filter(ProcessingTask.knowledge_base_id == kb_id)
            .order_by(ProcessingTask.created_at.desc())
            .all()
        )

    # -------------------------------
    # CONVENIENCE HELPERS
    # -------------------------------
    def mark_processing(self, task_id: int):
        return self.update_status(task_id, "processing")

    def mark_completed(self, task_id: int):
        return self.update_status(task_id, "completed")

    def mark_failed(self, task_id: int, error_message: str):
        return self.update_status(task_id, "failed", error_message)
