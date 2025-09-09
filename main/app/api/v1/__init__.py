from fastapi import APIRouter
from .api_key.router import router as api_key_router

v1_router = APIRouter()
v1_router.include_router(
    api_key_router, prefix="/api-key", tags=["v1 API Keys"]
)
