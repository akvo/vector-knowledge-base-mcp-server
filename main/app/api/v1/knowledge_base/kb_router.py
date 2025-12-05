import logging
from typing import List, Any, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload, lazyload, noload
from sqlalchemy import or_

from app.db.connection import get_session
from app.core.security import get_api_key
from app.models.api_key import APIKey
from app.models.knowledge import KnowledgeBase
from app.services.kb_service import KnowledgeBaseService
from app.services.document_service import DocumentService
from app.api.v1.knowledge_base.schema import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    PaginatedKnowledgeBaseResponse,
)

from app.mcp.mcp_main import mcp
from app.mcp.resources.kb_resources import load_kb_resources
from app.tasks.kb_cleanup_task import cleanup_kb_task
from app.services.processing_task_service import ProcessingTaskService

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
        List[KnowledgeBaseResponse], PaginatedKnowledgeBaseResponse
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
        False, description="Return paginated response"
    ),
    search: Optional[str] = Query(
        None, description="Search by name or description"
    ),
    kb_ids: Optional[List[int]] = Query(
        None, description="Filter knowledge bases by definend kb IDs"
    ),
    db: Session = Depends(get_session),
    api_key: APIKey = Depends(get_api_key),
) -> Any:
    """
    List knowledge bases.
    Supports pagination, search, and optional total wrapping.
    """
    query = db.query(KnowledgeBase)

    # Handle filtering by kb IDs
    if kb_ids:
        query = query.filter(KnowledgeBase.id.in_(kb_ids))

    # 🔍 Search in BOTH name + description
    if search:
        search = search.strip()
        like = f"%{search}%"
        query = query.filter(
            or_(
                KnowledgeBase.name.ilike(like),
                KnowledgeBase.description.ilike(like),
            )
        )

    # ⚡ Load documents only when requested
    if with_documents:
        query = query.options(joinedload(KnowledgeBase.documents))
    else:
        # Prevent any document loading — do NOT load relationship
        query = query.options(noload(KnowledgeBase.documents))

    # Pagination
    items = query.offset(skip).limit(limit).all()

    # 🔒 Ensure documents array is always present but empty when requested
    if not with_documents:
        for kb in items:
            kb.documents = []  # avoids lazy loading
    else:
        for kb in items:
            doc_service = DocumentService(kb_id=kb.id, db=db)
            for doc in kb.documents:
                url = doc_service._build_direct_url(file_path=doc.file_path)
                setattr(doc, "file_url", url)

    # Return simple list
    if not include_total:
        return items

    # Pagination metadata
    total = query.count()
    page = skip // limit + 1

    return PaginatedKnowledgeBaseResponse(
        total=total,
        page=page,
        size=len(items),
        data=items,
    )


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
    else:
        doc_service = DocumentService(kb_id=kb.id, db=db)
        for doc in kb.documents:
            url = doc_service._build_direct_url(file_path=doc.file_path)
            setattr(doc, "file_url", url)
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
    api_key=Depends(get_api_key),
):
    service = KnowledgeBaseService(db)
    processing_task_service = ProcessingTaskService(db)

    # ensure KB exists
    service.get_kb_by_id(kb_id=kb_id)

    # create processing task record
    task = processing_task_service.create_task(kb_id=kb_id)

    # delete DB record only
    service.delete_kb_record_only(kb_id=kb_id)

    # schedule async cleanup
    celery_task = cleanup_kb_task.delay(kb_id=kb_id, task_id=task.id)
    logger.info(f"Scheduled KB cleanup task {celery_task.id} for KB {kb_id}")

    processing_task_service.update_status(
        task_id=task.id, celery_task_id=celery_task.id
    )

    return {
        "message": "Knowledge base deleted. Cleanup scheduled.",
        "kb_id": kb_id,
    }
