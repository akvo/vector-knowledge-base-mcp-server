from datetime import datetime
from sqlalchemy.orm import Session
from app.models.api_key import APIKey


class TestAPIKeyModel:
    def test_generate_api_key(self):
        """APIKey.generate_api_key should produce unique keys"""
        key1 = APIKey.generate_api_key()
        key2 = APIKey.generate_api_key()

        assert isinstance(key1, str)
        assert isinstance(key2, str)
        assert key1 != key2

    def test_create_api_key(self, session: Session):
        """Creating an APIKey should set default values and timestamps"""
        api_key = APIKey(name="Test Key")
        api_key.key = APIKey.generate_api_key()

        session.add(api_key)
        session.commit()
        session.refresh(api_key)

        assert api_key.id is not None
        assert api_key.key is not None
        assert api_key.name == "Test Key"
        assert api_key.is_active is True
        assert api_key.last_used_at is None
        assert isinstance(api_key.created_at, datetime)
        assert isinstance(api_key.updated_at, datetime)

    def test_mark_used(self, session: Session):
        """APIKey.mark_used should update last_used_at timestamp"""
        api_key = APIKey(name="Used Key")
        api_key.key = APIKey.generate_api_key()
        session.add(api_key)
        session.commit()
        session.refresh(api_key)

        # Before marking used
        assert api_key.last_used_at is None

        # After mark_used
        api_key.mark_used()
        session.commit()
        session.refresh(api_key)

        assert api_key.last_used_at is not None
        assert isinstance(api_key.last_used_at, datetime)
