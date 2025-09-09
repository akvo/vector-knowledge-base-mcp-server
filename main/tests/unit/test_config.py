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
    assert config.settings.minio_endpoint == "localhost:9000"
    assert config.settings.minio_access_key == "minioadmin"
    assert config.settings.minio_secret_key == "minioadmin"
    assert config.settings.minio_bucket_name == "documents"
    assert config.settings.chroma_db_host == "localhost"
    assert config.settings.chroma_db_port == 8000


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


def test_set_settings_value(monkeypatch):
    """DATABASE_URL containing % should be converted to %%."""
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db/db")
    monkeypatch.setenv("MINIO_ENDPOINT", "minio:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "minioadmin")
    monkeypatch.setenv("MINIO_SECRET_KEY", "minioadmin")
    monkeypatch.setenv("MINIO_BUCKET_NAME", "documents")
    monkeypatch.setenv("CHROMA_DB_HOST", "chromadb")
    monkeypatch.setenv("CHROMA_DB_PORT", "8000")

    import app.core.config as config

    importlib.reload(config)

    assert config.settings.database_url == "postgresql://user:pass@db/db"
    assert config.settings.testing is True
    assert config.settings.minio_endpoint == "minio:9000"
    assert config.settings.minio_access_key == "minioadmin"
    assert config.settings.minio_secret_key == "minioadmin"
    assert config.settings.minio_bucket_name == "documents"
    assert config.settings.chroma_db_host == "chromadb"
    assert config.settings.chroma_db_port == 8000
