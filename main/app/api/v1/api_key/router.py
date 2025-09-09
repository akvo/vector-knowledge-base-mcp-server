from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.db.connection import get_session
from app.services.api_key_service import APIKeyService
from . import schema

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=List[schema.APIKey], name="v1_list_api_keys")
def read_api_keys(
    db: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve API keys.
    """
    api_keys = APIKeyService.get_api_keys(db=db, skip=skip, limit=limit)
    return api_keys


@router.post("", response_model=schema.APIKey, name="v1_create_api_key")
def create_api_key(
    *,
    db: Session = Depends(get_session),
    api_key_in: schema.APIKeyCreate,
) -> Any:
    """
    Create new API key.
    """
    api_key = APIKeyService.create_api_key(db=db, name=api_key_in.name)
    logger.info(f"API key created: {api_key.key}")
    return api_key


@router.put("/{id}", response_model=schema.APIKey, name="v1_update_api_key")
def update_api_key(
    *,
    db: Session = Depends(get_session),
    id: int,
    api_key_in: schema.APIKeyUpdate,
) -> Any:
    """
    Update API key.
    """
    api_key = APIKeyService.get_api_key(db=db, api_key_id=id)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key = APIKeyService.update_api_key(
        db=db, api_key=api_key, update_data=api_key_in
    )
    logger.info(f"API key updated: {api_key.key}")
    return api_key


@router.delete("/{id}", response_model=schema.APIKey, name="v1_delete_api_key")
def delete_api_key(
    *,
    db: Session = Depends(get_session),
    id: int,
) -> Any:
    """
    Delete API key.
    """
    api_key = APIKeyService.get_api_key(db=db, api_key_id=id)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    APIKeyService.delete_api_key(db=db, api_key=api_key)
    logger.info(f"API key deleted: {api_key.key}")
    return api_key
