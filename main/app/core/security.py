from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.db.connection import get_session
from app.services.api_key_service import APIKeyService
from app.models.api_key import APIKey
from app.core.config import settings

"""
Expect:
- Authorization: API-Key <key>
    for knowledge base routes using generated api key authentication
- Authorization: Admin-Key <key>
    for api key routes using static admin api key from environment variable
"""
authorization_header = APIKeyHeader(name="Authorization", auto_error=False)


async def get_api_key(
    authorization: str = Security(authorization_header),
    db: Session = Depends(get_session),
) -> APIKey:
    # 1. Get API Key
    if not authorization or not authorization.startswith("API-Key "):
        raise HTTPException(status_code=401, detail="API key required")

    raw_key = authorization.split(" ", 1)[1]

    # 2. Validate api key
    db_key = APIKeyService.get_api_key_by_key(db, raw_key)
    if not db_key or not db_key.is_active:
        raise HTTPException(
            status_code=401, detail="Invalid or inactive API key"
        )

    # 3. Update last_used
    APIKeyService.update_last_used(db, db_key)

    return db_key


def verify_admin_key(
    authorization: str = Security(authorization_header),
) -> bool:
    # 1. Get API Key
    if not authorization or not authorization.startswith("Admin-Key "):
        raise HTTPException(status_code=401, detail="Admin API key required")

    raw_key = authorization.split(" ", 1)[1]

    # 2. Validate api key
    if raw_key != settings.admin_api_key:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required",
        )
    return True
