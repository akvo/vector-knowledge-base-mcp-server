import logging
from celery.exceptions import MaxRetriesExceededError

from app.db.connection import get_session
from app.services.kb_service import KnowledgeBaseService
from app.services.processing_task_service import ProcessingTaskService
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="tasks.cleanup_kb_task",
    bind=True,
    max_retries=5,
    default_retry_delay=20,
    autoretry_for=(Exception,),
)
def cleanup_kb_task(self, kb_id: int, task_id: int = None):
    """
    Celery task to clean up resources associated with a knowledge base.
    1. Deletes files from MinIO.
    2. Cleans up entries in Chroma vector database.
    3. Retries on failure with exponential backoff.
    4. Logs progress and errors.
    """

    db = next(get_session())
    processing_task_service = ProcessingTaskService(db)
    processing_task_service.mark_processing(task_id=task_id)

    try:
        service = KnowledgeBaseService(db)

        logger.info(
            f"[KB CLEANUP] Starting cleanup for KB {kb_id}. "
            f"Attempt {self.request.retries + 1}"
        )

        # CALL SERVICE METHOD
        service.cleanup_kb_resources(kb_id)

        logger.info(f"[KB CLEANUP] Completed cleanup for KB {kb_id}")

        processing_task_service.mark_completed(task_id=task_id)

        return {"kb_id": kb_id, "status": "deleted"}

    except Exception as e:
        processing_task_service.mark_failed(
            task_id=task_id, error_message=str(e)
        )

        attempt = self.request.retries + 1
        delay = min(300, 20 * (2**attempt))  # exponential backoff

        logger.error(
            f"[KB CLEANUP] Error cleaning KB {kb_id}: {e}. "
            f"Retrying in {delay}s (attempt {attempt}/5)"
        )

        try:
            raise self.retry(exc=e, countdown=delay)
        except MaxRetriesExceededError:
            logger.critical(
                f"[KB CLEANUP] Permanent FAILURE cleaning KB {kb_id}. "
                "Manual action required."
            )

            raise

    finally:
        db.close()
