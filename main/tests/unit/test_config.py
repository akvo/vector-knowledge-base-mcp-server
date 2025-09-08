import importlib


def test_default_settings(monkeypatch):
    """Default settings should be non-testing with a valid DB URL."""
    monkeypatch.delenv("TESTING", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")

    import app.core.config as config

    importlib.reload(config)

    assert (
        config.settings.database_url == "postgresql://user:pass@localhost/db"
    )
    assert config.settings.testing is False


def test_testing_true(monkeypatch):
    """If TESTING=true, settings.testing must be True."""
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db:5432/dbname")

    import app.core.config as config

    importlib.reload(config)

    assert config.settings.testing is True
    assert config.settings.database_url.startswith("postgresql://")


def test_database_url_escape_percent(monkeypatch):
    """DATABASE_URL containing % should be converted to %%."""
    monkeypatch.setenv("TESTING", "false")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pa%ss@db/db")

    import app.core.config as config

    importlib.reload(config)

    assert "%%" in config.settings.database_url
