import logging

from typing import List, Any
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session
from minio.error import MinioException

from app.core.config import settings
from app.db.connection import get_session
from app.core.security import get_api_key
from app.models.api_key import APIKey
from app.models.knowledge import (
    KnowledgeBase,
    Document,
)
from .schema import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)
from app.services.minio_service import get_minio_client
from app.services.embedding_factory import EmbeddingsFactory
from app.services.chromadb_service import ChromaVectorStore

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "", response_model=KnowledgeBaseResponse, name="v1_create_knowledge_base"
)
def create_knowledge_base(
    *,
    db: Session = Depends(get_session),
    kb_in: KnowledgeBaseCreate,
    api_key: APIKey = Depends(get_api_key),
) -> Any:
    """
    Create new knowledge base.
    """
    kb = KnowledgeBase(name=kb_in.name, description=kb_in.description)
    db.add(kb)
    db.commit()
    db.refresh(kb)
    logger.info(f"Knowledge base created: {kb.name}")
    return kb


@router.get(
    "",
    response_model=List[KnowledgeBaseResponse],
    name="v1_list_knowledge_bases",
)
def get_knowledge_bases(
    db: Session = Depends(get_session),
    api_key: APIKey = Depends(get_api_key),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve knowledge bases.
    """
    knowledge_bases = db.query(KnowledgeBase).offset(skip).limit(limit).all()
    return knowledge_bases


@router.get(
    "/{kb_id}",
    response_model=KnowledgeBaseResponse,
    name="v1_get_knowledge_base",
)
def get_knowledge_base(
    *,
    db: Session = Depends(get_session),
    kb_id: int,
    api_key: APIKey = Depends(get_api_key),
) -> Any:
    """
    Get knowledge base by ID.
    """
    from sqlalchemy.orm import joinedload

    kb = (
        db.query(KnowledgeBase)
        .options(
            joinedload(KnowledgeBase.documents).joinedload(
                Document.processing_tasks
            )
        )
        .filter(KnowledgeBase.id == kb_id)
        .first()
    )

    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    return kb


@router.put(
    "/{kb_id}",
    response_model=KnowledgeBaseResponse,
    name="v1_update_knowledge_base",
)
def update_knowledge_base(
    *,
    db: Session = Depends(get_session),
    kb_id: int,
    kb_in: KnowledgeBaseUpdate,
    api_key: APIKey = Depends(get_api_key),
) -> Any:
    """
    Update knowledge base.
    """
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()

    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    for field, value in kb_in.dict(exclude_unset=True).items():
        setattr(kb, field, value)

    db.add(kb)
    db.commit()
    db.refresh(kb)
    logger.info(f"Knowledge base updated: {kb.name}")
    return kb


@router.delete("/{kb_id}", name="v1_delete_knowledge_base")
async def delete_knowledge_base(
    *,
    db: Session = Depends(get_session),
    kb_id: int,
    api_key: APIKey = Depends(get_api_key),
) -> Any:
    """
    Delete knowledge base and all associated resources.
    """
    logger = logging.getLogger(__name__)

    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    try:
        # Get all document file paths before deletion
        # document_paths = [doc.file_path for doc in kb.documents]

        # Initialize services
        minio_client = get_minio_client()
        embeddings = EmbeddingsFactory.create()

        vector_store = ChromaVectorStore(
            collection_name=f"kb_{kb_id}",
            embedding_function=embeddings,
        )

        # Clean up external resources first
        cleanup_errors = []

        # 1. Clean up MinIO files
        try:
            # Delete all objects with prefix kb_{kb_id}/
            objects = minio_client.list_objects(
                settings.minio_bucket_name, prefix=f"kb_{kb_id}/"
            )
            for obj in objects:
                minio_client.remove_object(
                    settings.minio_bucket_name, obj.object_name
                )
            logger.info(f"Cleaned up MinIO files for knowledge base {kb_id}")
        except MinioException as e:
            cleanup_errors.append(f"Failed to clean up MinIO files: {str(e)}")
            logger.error(f"MinIO cleanup error for kb {kb_id}: {str(e)}")

        # 2. Clean up vector store
        try:
            vector_store.delete_collection()
            logger.info(f"Cleaned up vector store for knowledge base {kb_id}")
        except Exception as e:
            cleanup_errors.append(f"Failed to clean up vector store: {str(e)}")
            logger.error(
                f"Vector store cleanup error for kb {kb_id}: {str(e)}"
            )

        # Finally, delete database records in a single transaction
        db.delete(kb)
        db.commit()

        # Report any cleanup errors in the response
        if cleanup_errors:
            return {
                "message": "KB deleted with cleanup warnings",
                "warnings": cleanup_errors,
            }

        return {
            "message": "KB and all associated resources deleted successfully"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete knowledge base {kb_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete knowledge base: {str(e)}",
        )
