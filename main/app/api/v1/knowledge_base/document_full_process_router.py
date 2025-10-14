import logging

from typing import List
from fastapi import (
    APIRouter,
    UploadFile,
    BackgroundTasks,
    Depends,
)
from sqlalchemy.orm import Session

from app.db.connection import get_session
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/knowledge-base")


@router.post(
    "/{kb_id}/documents/full-process", name="v1_full_process_documents"
)
async def full_process_documents(
    kb_id: int,
    files: List[UploadFile],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session),
):
    """
    Upload + process documents in one call (no preview).
    """
    doc_service = DocumentService(kb_id, db)

    # 1️⃣ Upload documents
    upload_results = await doc_service.upload_documents(files)

    # 2️⃣ Immediately schedule background processing
    return await doc_service.process_documents(
        upload_results, background_tasks
    )
