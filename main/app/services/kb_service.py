import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException
from minio.error import MinioException

from app.models.knowledge import KnowledgeBase
from app.services.minio_service import get_minio_client
from app.services.embedding_factory import EmbeddingsFactory
from app.services.chromadb_service import ChromaVectorStore
from app.core.config import settings

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    def __init__(self, db: Session):
        self.db = db

    async def delete_kb(self, kb_id: int):
        kb = (
            self.db.query(KnowledgeBase)
            .filter(KnowledgeBase.id == kb_id)
            .first()
        )
        if not kb:
            raise HTTPException(
                status_code=404, detail="Knowledge base not found"
            )

        cleanup_errors = []

        try:
            # 1. MinIO cleanup
            try:
                minio_client = get_minio_client()
                objects = minio_client.list_objects(
                    settings.minio_bucket_name, prefix=f"kb_{kb_id}/"
                )
                for obj in objects:
                    minio_client.remove_object(
                        settings.minio_bucket_name, obj.object_name
                    )
                logger.info(f"Cleaned MinIO files for KB {kb_id}")
            except MinioException as e:
                cleanup_errors.append(f"MinIO cleanup failed: {str(e)}")
                logger.error(f"MinIO cleanup error for KB {kb_id}: {str(e)}")

            # 2. Vector store cleanup
            try:
                embeddings = EmbeddingsFactory.create()
                vector_store = ChromaVectorStore(
                    collection_name=f"kb_{kb_id}",
                    embedding_function=embeddings,
                )
                vector_store.delete_collection()
                logger.info(f"Deleted vector store for KB {kb_id}")
            except Exception as e:
                cleanup_errors.append(f"Vector store cleanup failed: {str(e)}")
                logger.error(
                    f"Vector store cleanup error for KB {kb_id}: {str(e)}"
                )

            # 3. Database cleanup
            self.db.delete(kb)
            self.db.commit()

            if cleanup_errors:
                return {
                    "message": "KB deleted with warnings",
                    "warnings": cleanup_errors,
                }
            msg = "KB and all associated resources deleted successfully"
            return {"message": msg}

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete knowledge base {kb_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete knowledge base: {str(e)}",
            )
