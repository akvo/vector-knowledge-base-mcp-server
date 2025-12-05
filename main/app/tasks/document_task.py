import logging
import asyncio

from app.services.document_processor import process_document_background
from app.db.connection import get_session
from app.celery_app import celery_app


logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.process_document_task")
def process_document_task(
    kb_id: int,
    task_id: int,
    temp_path: str,
    file_name: str,
    file_size: int,
):
    """
    Celery version of process_document_background.
    """

    logger.info(f"[Celery] Processing upload {task_id} for KB {kb_id}")

    # DB session must be created inside worker thread
    db = next(get_session())

    try:
        asyncio.run(
            process_document_background(
                temp_path=temp_path,
                file_name=file_name,
                file_size=file_size,
                kb_id=kb_id,
                task_id=task_id,
                db=db,
            )
        )
        db.close()
        return {"task_id": task_id, "status": "completed"}

    except Exception as e:
        logger.error(f"[Celery] Error processing {task_id}: {e}")
        db.rollback()
        db.close()
        raise
