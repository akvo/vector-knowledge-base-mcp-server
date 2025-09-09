from typing import List, Any
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session
import logging

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


# TODO:: SETUP MINIO CHROMA and route related to documents and chunks
