import importlib
import pytest

import app.db.connection as conn
from app.core import config
from app.core.config import settings


@pytest.mark.unit
class TestGetDbUrl:

    def test_get_db_url_testing(self, monkeypatch):
        """Should append _test to DB URL when TESTING=True."""
        monkeypatch.setenv("TESTING", "true")
        importlib.reload(config)
        importlib.reload(conn)

        db_url = conn.get_db_url()
        assert db_url.endswith("_test")

    def test_make_sure_get_db_url_not_added_extra_suffix(self, monkeypatch):
        """Should not append _test if already present in DB URL."""
        monkeypatch.setenv("TESTING", "true")
        monkeypatch.setenv("DATABASE_URL", f"{settings.database_url}_test")
        importlib.reload(config)
        importlib.reload(conn)

        db_url = conn.get_db_url()
        assert db_url == f"{settings.database_url}_test"
