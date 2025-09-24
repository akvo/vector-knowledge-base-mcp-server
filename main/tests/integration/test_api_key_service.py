import pytest
from datetime import datetime

from app.schemas.api_key_schema import APIKeyUpdate
from app.services.api_key_service import APIKeyService


@pytest.mark.usefixtures("session")
class TestAPIKeyService:
    def test_create_api_key(self, session):
        """APIKeyService.create_api_key should create a valid API key"""
        api_key = APIKeyService.create_api_key(session, name="My Key")

        assert api_key.id is not None
        assert api_key.key.startswith("sk-")
        assert api_key.is_active is True
        assert api_key.name == "My Key"

    def test_get_api_keys(self, session):
        """APIKeyService.get_api_keys should list multiple keys"""
        APIKeyService.create_api_key(session, "Key1")
        APIKeyService.create_api_key(session, "Key2")

        keys = APIKeyService.get_api_keys(session)
        assert len(keys) >= 2

    def test_get_api_key_by_id_and_key(self, session):
        """APIKeyService should fetch APIKey by id and by key"""
        api_key = APIKeyService.create_api_key(session, "KeyTest")

        fetched = APIKeyService.get_api_key(session, api_key.id)
        assert fetched.id == api_key.id

        fetched2 = APIKeyService.get_api_key_by_key(session, api_key.key)
        assert fetched2.key == api_key.key

    def test_update_api_key(self, session):
        """APIKeyService.update_api_key should update name and is_active"""
        api_key = APIKeyService.create_api_key(session, "OldName")

        updated = APIKeyService.update_api_key(
            session, api_key, APIKeyUpdate(name="NewName")
        )
        assert updated.name == "NewName"

        updated = APIKeyService.update_api_key(
            session, api_key, APIKeyUpdate(is_active=False)
        )
        assert updated.is_active is False

    def test_update_last_used(self, session):
        """APIKeyService.update_last_used should set last_used_at"""
        api_key = APIKeyService.create_api_key(session, "KeyUsed")
        assert api_key.last_used_at is None

        updated = APIKeyService.update_last_used(session, api_key)
        assert updated.last_used_at is not None
        assert isinstance(updated.last_used_at, datetime)

    def test_delete_api_key(self, session):
        """APIKeyService.delete_api_key should remove the key"""
        api_key = APIKeyService.create_api_key(session, "ToDelete")
        APIKeyService.delete_api_key(session, api_key)

        fetched = APIKeyService.get_api_key(session, api_key.id)
        assert fetched is None
