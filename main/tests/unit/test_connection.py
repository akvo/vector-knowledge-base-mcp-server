import importlib


def test_get_db_url_testing(monkeypatch):
    """Should append _test to DB URL when TESTING=True."""
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")

    # reload settings agar env terbaru kebaca
    import app.core.config as config

    importlib.reload(config)

    import app.db.connection as conn

    importlib.reload(conn)

    assert conn.get_db_url() == "postgresql://user:pass@localhost/db_test"


def test_get_db_url_non_testing(monkeypatch):
    """Should return DB URL as is when TESTING=False."""
    monkeypatch.setenv("TESTING", "false")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")

    import app.core.config as config

    importlib.reload(config)

    import app.db.connection as conn

    importlib.reload(conn)

    assert conn.get_db_url() == "postgresql://user:pass@localhost/db"
