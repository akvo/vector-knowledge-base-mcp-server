from fastapi import APIRouter

from .api_key.router import router as api_key_router
from .knowledge_base.kb_router import router as kb_router
from .knowledge_base.document_router import router as document_router
from .knowledge_base.retrieval_router import router as retrieval_router

v1_router = APIRouter()

v1_router.include_router(
    api_key_router, prefix="/api-key", tags=["v1 API Keys"]
)
v1_router.include_router(
    kb_router, prefix="/knowledge-base", tags=["v1 Knowledge Base"]
)
v1_router.include_router(
    document_router, prefix="/knowledge-base", tags=["v1 Knowledge Base"]
)
v1_router.include_router(
    retrieval_router, prefix="/knowledge-base", tags=["v1 Knowledge Base"]
)
