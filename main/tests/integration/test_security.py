import pytest

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_api_key, verify_admin_key
from app.services.api_key_service import APIKeyService
from app.models.api_key import APIKey
from app.core.config import settings


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


class TestVerifyAdminKey:
    def test_valid_admin_key(self, monkeypatch):
        """verify_admin_key should pass if correct Admin-Key is provided"""
        header_value = f"Admin-Key {settings.admin_api_key}"
        assert verify_admin_key(authorization=header_value) is True

    def test_missing_header(self):
        """verify_admin_key should raise 401 if header is missing"""
        with pytest.raises(HTTPException) as exc:
            verify_admin_key(authorization=None)
        assert exc.value.status_code == 401
        assert exc.value.detail == "Admin API key required"

    def test_wrong_prefix(self):
        """
        verify_admin_key should raise 401 if header does not start with
        Admin-Key
        """
        with pytest.raises(HTTPException) as exc:
            verify_admin_key(authorization="API-Key something")
        assert exc.value.status_code == 401
        assert exc.value.detail == "Admin API key required"

    def test_invalid_admin_key(self, monkeypatch):
        """verify_admin_key should raise 403 if Admin-Key is incorrect"""
        monkeypatch.setattr(settings, "admin_api_key", "supersecret")

        with pytest.raises(HTTPException) as exc:
            verify_admin_key(authorization="Admin-Key wrongkey")
        assert exc.value.status_code == 403
        assert exc.value.detail == "Admin privileges required"
