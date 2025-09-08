import importlib

import app.db.connection as conn
from app.core import config


def test_get_db_url_testing(monkeypatch):
    """Should append _test to DB URL when TESTING=True."""
    monkeypatch.setenv("TESTING", "true")
    importlib.reload(config)
    importlib.reload(conn)

    db_url = conn.get_db_url()
    assert db_url.endswith("_test")
