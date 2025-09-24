import pytest

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_api_key
from app.services.api_key_service import APIKeyService
from app.models.api_key import APIKey


@pytest.mark.asyncio
class TestGetAPIKey:
    async def test_valid_key(self, session: Session):
        """
        get_api_key should return valid APIKey instance for correct header
        """
        # Create API key
        api_key = APIKeyService.create_api_key(session, name="Test Key")

        # Simulate header "Authorization: Api-Key <key>"
        header_value = f"API-Key {api_key.key}"
        db_key = await get_api_key(authorization=header_value, db=session)

        assert isinstance(db_key, APIKey)
        assert db_key.id == api_key.id
        assert db_key.name == "Test Key"

    async def test_missing_header(self, session: Session):
        """get_api_key should raise 401 if header is missing"""
        with pytest.raises(HTTPException) as exc:
            await get_api_key(authorization=None, db=session)
        assert exc.value.status_code == 401
        assert exc.value.detail == "API key required"

    async def test_invalid_key(self, session: Session):
        """get_api_key should raise 401 for invalid API key"""
        header_value = "API-Key invalidkey"
        with pytest.raises(HTTPException) as exc:
            await get_api_key(authorization=header_value, db=session)
        assert exc.value.status_code == 401
        assert exc.value.detail == "Invalid or inactive API key"

    async def test_inactive_key(self, session: Session):
        """get_api_key should raise 401 for inactive API key"""
        # Create inactive key
        api_key = APIKeyService.create_api_key(session, name="Inactive Key")
        api_key.is_active = False
        session.add(api_key)
        session.commit()

        header_value = f"API-Key {api_key.key}"
        with pytest.raises(HTTPException) as exc:
            await get_api_key(authorization=header_value, db=session)
        assert exc.value.status_code == 401
        assert exc.value.detail == "Invalid or inactive API key"
