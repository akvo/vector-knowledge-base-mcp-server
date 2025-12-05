# app/services/knowledge_base_service.py
import logging
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeBase
from app.services.minio_service import get_minio_client
from app.services.embedding_factory import EmbeddingsFactory
from app.services.chromadb_service import ChromaVectorStore
from app.core.config import settings

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    def __init__(self, db: Session):
        self.db = db

    def get_kb_by_id(self, kb_id: int):
        kb = (
            self.db.query(KnowledgeBase)
            .filter(KnowledgeBase.id == kb_id)
            .first()
        )
        if not kb:
            raise HTTPException(
                status_code=404, detail="Knowledge base not found"
            )

        return kb

    def delete_kb_record_only(self, kb_id: int):
        kb = self.get_kb_by_id(kb_id=kb_id)

        try:
            self.db.delete(kb)
            self.db.commit()

            logger.info(f"[KB DELETE] DB record deleted for KB {kb_id}")

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"[KB DELETE] Failed DB delete for KB {kb_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete knowledge base: {str(e)}",
            )

    def cleanup_kb_resources(self, kb_id: int):
        logger.info(f"[KB CLEANUP] Running cleanup for KB {kb_id}")

        # 1. Cleanup MinIO
        try:
            minio_client = get_minio_client()
            prefix = f"kb_{kb_id}/"

            objects = minio_client.list_objects(
                settings.minio_bucket_name, prefix=prefix
            )

            for obj in objects:
                minio_client.remove_object(
                    settings.minio_bucket_name, obj.object_name
                )

            logger.info(f"[KB CLEANUP] MinIO files removed for KB {kb_id}")

        except Exception as e:
            logger.error(f"[KB CLEANUP] MinIO cleanup failed: {str(e)}")
            raise

        # 2. Cleanup Chroma vector DB
        try:
            embeddings = EmbeddingsFactory.create()

            vector_store = ChromaVectorStore(
                collection_name=f"kb_{kb_id}",
                embedding_function=embeddings,
            )

            vector_store.delete_collection()

            logger.info(f"[KB CLEANUP] Chroma vectors removed for KB {kb_id}")

        except Exception as e:
            logger.error(f"[KB CLEANUP] Chroma cleanup failed: {str(e)}")
            raise
