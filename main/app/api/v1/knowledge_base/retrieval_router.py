from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.connection import get_session
from app.core.security import get_api_key
from app.models.api_key import APIKey
from app.models.knowledge import KnowledgeBase
from app.services.document_service import DocumentService
from app.api.v1.knowledge_base.schema import TestRetrievalRequest

router = APIRouter()


@router.post("/test-retrieval", name="v1_test_retrieval")
async def test_retrieval(
    request: TestRetrievalRequest,
    db: Session = Depends(get_session),
    api_key: APIKey = Depends(get_api_key),
):
    kb = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.id == request.kb_id)
        .first()
    )
    if not kb:
        raise HTTPException(
            status_code=404, detail=f"Knowledge base {request.kb_id} not found"
        )

    service = DocumentService(request.kb_id, db)
    results = service.search(request.query, request.top_k)
    return {"results": results}
