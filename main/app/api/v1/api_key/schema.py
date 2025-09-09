from typing import Optional
from datetime import datetime

from app.schemas.api_key_schema import APIKeyBase, APIKeyUpdate


class APIKeyCreate(APIKeyBase):
    pass


class APIKeyUpdate(APIKeyUpdate):
    pass


class APIKey(APIKeyBase):
    id: int
    key: str
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class APIKeyInDB(APIKey):
    pass
