import logging

from typing import List, Optional, Union, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, BackgroundTasks, Query
from sqlalchemy.orm import Session

from app.db.connection import get_session
from app.core.security import get_api_key
from app.models.api_key import APIKey
from app.models.knowledge import Document
from app.services.document_service import DocumentService
from app.services.document_processor import PreviewResult
from app.api.v1.knowledge_base.schema import (
    PreviewRequest,
    DocumentResponse,
    DocumentUploadItem,
    PaginatedDocumentResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/{kb_id}/documents/upload", name="v1_upload_kb_documents")
async def upload_kb_documents(
    kb_id: int,
    files: List[UploadFile],
    db: Session = Depends(get_session),
    api_key: APIKey = Depends(get_api_key),
):
    service = DocumentService(kb_id, db)
    return await service.upload_documents(files)


@router.post("/{kb_id}/documents/preview", name="v1_preview_kb_documents")
async def preview_kb_documents(
    kb_id: int,
    preview_request: PreviewRequest,
    db: Session = Depends(get_session),
    api_key: APIKey = Depends(get_api_key),
) -> Dict[int, PreviewResult]:
    service = DocumentService(kb_id, db)
    return await service.preview_documents(preview_request)


@router.post("/{kb_id}/documents/process", name="v1_process_kb_documents")
async def process_kb_documents(
    kb_id: int,
    upload_results: List[dict],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session),
    api_key: APIKey = Depends(get_api_key),
):
    service = DocumentService(kb_id, db)
    return await service.process_documents(upload_results, background_tasks)


@router.post("/cleanup", name="v1_cleanup_temp_files")
async def cleanup_temp_files(
    db: Session = Depends(get_session),
    api_key: APIKey = Depends(get_api_key),
):
    service = DocumentService(None, db)
    return await service.cleanup_temp_files()


@router.get(
    "/{kb_id}/documents",
    response_model=Union[List[DocumentResponse], PaginatedDocumentResponse],
    name="v1_list_kb_documents",
)
async def list_kb_documents(
    kb_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    include_total: bool = Query(
        False, description="Return paginated response"
    ),
    search: Optional[str] = Query(
        None, description="Search by partial filename"
    ),
    db: Session = Depends(get_session),
    api_key: APIKey = Depends(get_api_key),
):
    """
    List documents belonging to a Knowledge Base.
    Supports pagination, search, and optional total wrapping.
    """
    # TODO:: when fetch documents, please also check to document_uploads table
    query = db.query(Document).filter(Document.knowledge_base_id == kb_id)

    if search:
        search = search.strip()
        query = query.filter(Document.file_name.ilike(f"%{search}%"))

    # Get paginated items
    items = query.offset(skip).limit(limit).all()

    # inject URL + file info into each Document ORM output
    service = DocumentService(kb_id, db)

    for doc in items:
        url = service._build_direct_url(doc.file_path)
        # Dynamically attach extra fields without schema change
        setattr(doc, "file_url", url)

    # If no pagination wrapper requested → return plain list
    if not include_total:
        return items

    # Compute total ONLY when requested
    total = query.count()

    # Convert skip/limit to page number
    page = skip // limit + 1

    return PaginatedDocumentResponse(
        total=total,
        page=page,
        size=len(items),
        data=items,
    )


@router.get(
    "/{kb_id}/documents/upload",
    response_model=List[DocumentUploadItem],
    name="v1_get_kb_documents_upload",
)
async def get_kb_documents_upload(
    kb_id: int,
    db: Session = Depends(get_session),
    api_key: APIKey = Depends(get_api_key),
):
    """
    Fetch all documents uploaded belonging to a Knowledge Base (by kb_id).
    """
    service = DocumentService(kb_id, db)
    return service.get_documents_upload()


@router.get("/{kb_id}/documents/tasks", name="v1_get_processing_tasks")
async def get_processing_tasks(
    kb_id: int,
    task_ids: str = Query(...),
    db: Session = Depends(get_session),
    api_key: APIKey = Depends(get_api_key),
):
    service = DocumentService(kb_id, db)
    return await service.get_processing_tasks(task_ids)


@router.get(
    "/{kb_id}/documents/{doc_id}",
    response_model=DocumentResponse,
    name="v1_get_document",
)
async def get_document(
    kb_id: int,
    doc_id: int,
    db: Session = Depends(get_session),
    api_key: APIKey = Depends(get_api_key),
) -> Any:
    service = DocumentService(kb_id, db)
    return await service.get_document(doc_id)


@router.get(
    "/{kb_id}/documents/{document_id}/view",
    name="v1_view_kb_document",
)
async def get_kb_document_file(
    kb_id: int,
    document_id: int,
    db: Session = Depends(get_session),
    api_key: APIKey = Depends(get_api_key),
):
    service = DocumentService(kb_id, db)
    return await service.get_presigned_file_info(document_id)


@router.delete(
    "/{kb_id}/documents/{document_id}",
    name="v1_delete_kb_document",
)
async def delete_kb_document(
    kb_id: int,
    document_id: int,
    db: Session = Depends(get_session),
    api_key: APIKey = Depends(get_api_key),
):
    service = DocumentService(kb_id, db)
    return await service.delete_document(document_id)
