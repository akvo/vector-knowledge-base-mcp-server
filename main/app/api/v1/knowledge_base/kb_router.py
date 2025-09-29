import logging
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.db.connection import get_session
from app.core.security import get_api_key
from app.models.api_key import APIKey
from app.models.knowledge import KnowledgeBase
from app.services.kb_service import KnowledgeBaseService
from app.api.v1.knowledge_base.schema import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
)

from app.mcp.mcp_main import mcp
from app.mcp.resources.kb_resources import load_kb_resources

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "", response_model=KnowledgeBaseResponse, name="v1_create_knowledge_base"
)
def create_knowledge_base(
    kb_in: KnowledgeBaseCreate,
    db: Session = Depends(get_session),
    api_key: APIKey = Depends(get_api_key),
) -> Any:
    kb = KnowledgeBase(name=kb_in.name, description=kb_in.description)
    db.add(kb)
    db.commit()
    db.refresh(kb)
    logger.info(f"Knowledge base created: {kb.name}")
    load_kb_resources(mcp=mcp)
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
    return db.query(KnowledgeBase).offset(skip).limit(limit).all()


@router.get(
    "/{kb_id}",
    response_model=KnowledgeBaseResponse,
    name="v1_get_knowledge_base",
)
def get_knowledge_base(
    kb_id: int,
    db: Session = Depends(get_session),
    api_key: APIKey = Depends(get_api_key),
) -> Any:
    kb = (
        db.query(KnowledgeBase)
        .options(joinedload(KnowledgeBase.documents))
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
    kb_id: int,
    kb_in: KnowledgeBaseUpdate,
    db: Session = Depends(get_session),
    api_key: APIKey = Depends(get_api_key),
) -> Any:
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
    kb_id: int,
    db: Session = Depends(get_session),
    api_key: APIKey = Depends(get_api_key),
):
    service = KnowledgeBaseService(db)
    return await service.delete_kb(kb_id)
