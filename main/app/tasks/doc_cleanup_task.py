import json
import logging

from app.celery_app import celery_app
from app.core.config import settings
from app.services.chromadb_service import ChromaVectorStore
from app.services.embedding_factory import EmbeddingsFactory
from app.services.minio_service import get_minio_client
from app.db.connection import get_session
from app.services.processing_task_service import ProcessingTaskService

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.cleanup_doc_task")
def cleanup_doc_task(payload: dict):
    """Celery task to cleanup document files from MinIO and Chroma."""
    db = next(get_session())
    task_service = ProcessingTaskService(db)

    task_id = payload.get("task_id")
    kb_id = payload["kb_id"]
    document_id = payload["document_id"]
    file_path = payload["file_path"]
    is_processed = payload["is_processed"]

    task_service.mark_processing(task_id=task_id)

    minio_deleted = False
    chroma_deleted = False

    # Delete from Chroma if processed
    error = {}
    if is_processed:
        try:
            vector_store = ChromaVectorStore(
                collection_name=f"kb_{kb_id}",
                embedding_function=EmbeddingsFactory.create(),
            )
            vector_store.delete(filter={"document_id": document_id})
            chroma_deleted = True
            logger.info(f"[DOC CLEANUP] Deleted from Chroma: {document_id}")
        except Exception as e:
            error["chroma"] = str(e)
            logger.warning(
                f"[DOC CLEANUP] Chroma cleanup failed ({document_id}): {e}"
            )

    # Delete from MinIO
    try:
        minio = get_minio_client()
        minio.remove_object(settings.minio_bucket_name, file_path)
        minio_deleted = True
        logger.info(f"[DOC CLEANUP] Deleted from MinIO: {file_path}")
    except Exception as e:
        error["minio"] = str(e)
        logger.warning(
            f"[DOC CLEANUP] MinIO cleanup failed ({file_path}): {e}"
        )

    # mark task as completed
    if not error:
        task_service.mark_completed(task_id=task_id)
    else:
        task_service.mark_failed(
            task_id=task_id, error_details=json.dumps(error)
        )

    return {
        "task_id": task_id,
        "minio_deleted": minio_deleted,
        "chroma_deleted": chroma_deleted,
    }
