import os
import sys
import time
import warnings
import pytest
import pytest_asyncio

from fastmcp import Client
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock, AsyncMock


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# -------------------------------
# ENV setup for testing
# -------------------------------
os.environ["TESTING"] = "1"

from app.db.connection import get_db_url, get_session  # noqa
from app.models.base import Base  # noqa
from app.services.api_key_service import APIKeyService  # noqa
from app.mcp.mcp_main import mcp_app  # noqa


# -------------------------------
# Helper functions
# -------------------------------
def check_test_db_url():
    db_url = get_db_url()
    err_msg = (
        f"⚠️ The database URL for tests must contain '_test'. Found: {db_url}"
    )
    if "_test" not in db_url:
        raise RuntimeError(err_msg)
    print(f"✅ Using test database URL: {db_url}")


def wait_for_db(max_retries: int = 10, delay: int = 2):
    engine = create_engine(get_db_url())
    for i in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception as e:
            print(f"DB not ready, retry {i+1}/{max_retries}: {e}")
            time.sleep(delay)
    raise RuntimeError("Database not available after retries")


# -------------------------------
# Apply migrations once per session
# -------------------------------
@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    check_test_db_url()
    wait_for_db()

    config = Config(os.path.join(BASE_DIR, "alembic.ini"))
    command.upgrade(config, "head")


# -------------------------------
# Database session fixture
# -------------------------------
@pytest.fixture
def session() -> Session:
    check_test_db_url()
    engine = create_engine(get_db_url())
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()

    # Truncate tables
    with engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(
                text(
                    f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE;'
                )
            )

    yield session
    session.close()


# -------------------------------
# FastAPI app and client fixtures
# -------------------------------
@pytest.fixture
def app(apply_migrations: None) -> FastAPI:
    from app.main import app

    check_test_db_url()
    engine = create_engine(get_db_url())
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_session] = override_get_db
    return app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as c:
        yield c


# -------------------------------
# API key fixture
# -------------------------------
@pytest.fixture(scope="function")
def api_key_value(session: Session) -> str:
    """Create a global API key for tests"""
    api_key = APIKeyService.create_api_key(session, "Global Test Key")
    return api_key.key


# -------------------------------
# Global mocks for external services
# -------------------------------
@pytest.fixture
def patch_external_services(monkeypatch, tmp_path):
    """
    Patch external services for
    document_processor, kb_query_service, chromadb_service:
    - MinIO client
    - EmbeddingsFactory
    - ChromaVectorStore
    - preview_document
    """
    from app.services import (
        document_processor,
        kb_query_service,
        chromadb_service,
        minio_service,
        document_service,
        kb_service,
    )

    # ---------- MinIO mock ----------
    mock_minio = MagicMock()

    def mock_fget_object(*args, **kwargs):
        file_path = kwargs.get("file_path") or args[2]
        dummy_file = tmp_path / "test.txt"
        dummy_file.write_text("dummy content")
        dummy_file.rename(file_path)

    mock_minio.fget_object.side_effect = mock_fget_object
    mock_minio.put_object.return_value = None
    mock_minio.copy_object.return_value = None
    mock_minio.remove_object.return_value = None
    monkeypatch.setattr(
        document_processor, "get_minio_client", lambda: mock_minio
    )
    monkeypatch.setattr(minio_service, "get_minio_client", lambda: mock_minio)
    monkeypatch.setattr(kb_service, "get_minio_client", lambda: mock_minio)
    monkeypatch.setattr(
        document_service, "get_minio_client", lambda: mock_minio
    )

    # ---------- Embeddings ----------
    mock_embeddings = MagicMock()
    mock_embeddings.create.return_value = MagicMock()
    monkeypatch.setattr(
        document_processor.EmbeddingsFactory, "create", lambda: mock_embeddings
    )
    monkeypatch.setattr(
        kb_query_service.EmbeddingsFactory, "create", lambda: mock_embeddings
    )
    monkeypatch.setattr(
        kb_service.EmbeddingsFactory, "create", lambda: mock_embeddings
    )
    monkeypatch.setattr(
        document_service.EmbeddingsFactory, "create", lambda: mock_embeddings
    )

    # ---------- Vector store ----------
    mock_vs = MagicMock()
    for method in [
        "add_documents",
        "add_embeddings",
        "delete",
        "delete_collection",
        "similarity_search",
        "similarity_search_with_score",
        "similarity_search_by_vector",
        "as_retriever",
    ]:
        setattr(mock_vs, method, MagicMock())

    monkeypatch.setattr(
        chromadb_service, "ChromaVectorStore", lambda *a, **k: mock_vs
    )
    monkeypatch.setattr(
        document_processor, "ChromaVectorStore", lambda *a, **k: mock_vs
    )
    monkeypatch.setattr(
        kb_query_service, "ChromaVectorStore", lambda *a, **k: mock_vs
    )
    monkeypatch.setattr(
        kb_service, "ChromaVectorStore", lambda *a, **k: mock_vs
    )
    monkeypatch.setattr(
        document_service, "ChromaVectorStore", lambda *a, **k: mock_vs
    )

    # Async retriever for kb_query_service
    mock_retriever = AsyncMock()
    mock_retriever.ainvoke.return_value = [
        type(
            "Doc", (), {"page_content": "mock content", "metadata": {"id": 1}}
        )()
    ]
    mock_vs.as_retriever.return_value = mock_retriever

    # Mock similarity search with score instead of retriever
    mock_vs.similarity_search_with_score.return_value = [
        (
            type(
                "Doc",
                (),
                {"page_content": "mock content", "metadata": {"id": 1}},
            )(),
            0.1,  # fake score
        )
    ]

    # ---------- Preview document ----------
    mock_preview = AsyncMock()
    mock_preview.return_value = document_processor.PreviewResult(
        chunks=[
            document_processor.TextChunk(
                content="hello", metadata={"page": 1}
            ),
            document_processor.TextChunk(
                content="world", metadata={"page": 2}
            ),
        ],
        total_chunks=2,
    )
    monkeypatch.setattr(document_processor, "preview_document", mock_preview)
    monkeypatch.setattr(document_service, "preview_document", mock_preview)

    return {
        "mock_minio": mock_minio,
        "mock_embeddings": mock_embeddings,
        "mock_vector_store": mock_vs,
        "mock_preview": mock_preview,
    }


# -------------------------------
# Fixture to patch MCP server vector store
# -------------------------------
@pytest.fixture
def patch_mcp_server_vector_store(monkeypatch):
    import base64
    import app.services.document_service as document_service

    mock_store = MagicMock(name="MockChromaVectorStore")
    mock_retriever = AsyncMock(name="MockRetriever")

    mock_doc = type(
        "Doc",
        (),
        {
            "page_content": base64.b64encode(
                b"hello world, functional content"
            ).decode("utf-8"),
            "metadata": {"id": 1},
        },
    )()

    mock_retriever.aget_relevant_documents.return_value = [mock_doc]
    mock_store.as_retriever.return_value = mock_retriever

    # return mock_store
    monkeypatch.setattr(
        document_service, "ChromaVectorStore", lambda *a, **k: mock_store
    )

    return mock_store


# -------------------------------
# MCP server and client fixtures
# -------------------------------
@pytest.fixture
def run_test_server(patch_mcp_server_vector_store):
    import uvicorn
    import requests

    from multiprocessing import Process
    from app.main import app as main_app

    os.environ["TESTING"] = "1"

    check_test_db_url()

    engine = create_engine(get_db_url())
    TestingSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    main_app.dependency_overrides[get_session] = override_get_db

    def run_uvicorn():
        uvicorn.run(main_app, host="127.0.0.1", port=8001, log_level="info")

    process = Process(target=run_uvicorn, daemon=True)
    process.start()

    # Wait server ready
    for _ in range(15):
        try:
            r = requests.get("http://127.0.0.1:8001/api/health")
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.5)
    else:
        process.terminate()
        process.join()
        raise RuntimeError("Server failed to start")

    yield "http://127.0.0.1:8001"

    process.terminate()
    process.join()


@pytest_asyncio.fixture
async def mcp_client(api_key_value: str, run_test_server: str):
    url = f"{run_test_server}/mcp/"
    async with Client(url, auth=f"API-Key {api_key_value}") as client:
        yield client
