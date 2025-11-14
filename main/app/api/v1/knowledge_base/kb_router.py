import logging
from typing import List, Any, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload, selectinload, noload, lazyload
from sqlalchemy import or_, func

from app.db.connection import get_session
from app.core.security import get_api_key
from app.models.api_key import APIKey
from app.models.knowledge import KnowledgeBase
from app.services.kb_service import KnowledgeBaseService
from app.api.v1.knowledge_base.schema import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    PaginatedKnowledgeBaseResponse,
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
    response_model=Union[
        List[KnowledgeBaseResponse],
        PaginatedKnowledgeBaseResponse,
    ],
    name="v1_list_knowledge_bases",
)
def get_knowledge_bases(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    with_documents: bool = Query(
        True, description="Include documents in response"
    ),
    include_total: bool = Query(
        False, description="Include total count wrapper"
    ),
    search: Optional[str] = Query(None, description="Search by name"),
    db: Session = Depends(get_session),
    api_key: APIKey = Depends(get_api_key),
):
    base_query = db.query(KnowledgeBase)

    # --- Search filter ---
    if search:
        base_query = base_query.filter(
            or_(
                KnowledgeBase.name.ilike(f"%{search}%"),
                KnowledgeBase.description.ilike(f"%{search}%"),
            )
        )

    # --- Optional total count ---
    total = None
    if include_total:
        total = base_query.with_entities(func.count(KnowledgeBase.id)).scalar()

    # --- Data query (paginated) ---
    data_query = base_query.order_by(KnowledgeBase.id)

    # Conditional loading of documents
    if with_documents:
        data_query = data_query.options(selectinload(KnowledgeBase.documents))
    else:
        data_query = data_query.options(noload(KnowledgeBase.documents))

    items = data_query.offset(skip).limit(limit).all()

    # --- Conditional response format ---
    if include_total:
        return PaginatedKnowledgeBaseResponse(total=total, items=items)

    return items


@router.get(
    "/{kb_id}",
    response_model=KnowledgeBaseResponse,
    name="v1_get_knowledge_base",
)
def get_knowledge_base(
    kb_id: int,
    with_documents: bool = Query(
        True, description="Include documents in response"
    ),
    db: Session = Depends(get_session),
    api_key: APIKey = Depends(get_api_key),
):
    query = db.query(KnowledgeBase)

    if with_documents:
        query = query.options(joinedload(KnowledgeBase.documents))
    else:
        # prevent lazy loading & return empty list
        query = query.options(lazyload(KnowledgeBase.documents))

    kb = query.filter(KnowledgeBase.id == kb_id).first()

    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # If skipping documents, force empty list (not lazy-loaded)
    if not with_documents:
        kb.documents = []

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
