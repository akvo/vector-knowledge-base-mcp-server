from typing import Optional
from pydantic import BaseModel


class APIKeyBase(BaseModel):
    name: str
    is_active: bool = True


class APIKeyUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
