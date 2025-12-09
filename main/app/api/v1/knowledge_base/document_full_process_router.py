import logging

from typing import List
from fastapi import (
    APIRouter,
    UploadFile,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.db.connection import get_session
from app.core.security import get_api_key
from app.models.knowledge import KnowledgeBase
from app.models.api_key import APIKey
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/{kb_id}/documents/full-process", name="v1_full_process_documents"
)
async def full_process_documents(
    kb_id: int,
    files: List[UploadFile],
    db: Session = Depends(get_session),
    api_key: APIKey = Depends(get_api_key),
):
    """
    Upload + process documents in one call (no preview).
    """
    try:
        # Ensure KB exists
        kb = db.query(KnowledgeBase).filter_by(id=kb_id).first()
        if not kb:
            raise HTTPException(
                status_code=404, detail="Knowledge base not found"
            )

        doc_service = DocumentService(kb_id, db)

        # 1️⃣ Upload documents
        upload_results = await doc_service.upload_documents(files)

        # 2️⃣ Process documents
        return await doc_service.process_documents(upload_results)

    except HTTPException:
        # Re-raise FastAPI HTTPExceptions directly
        raise
    except Exception as e:
        # Catch all unexpected errors
        logger.error("💥 Exception in full_process_documents", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
