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
from unittest.mock import patch, MagicMock


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# -------------------------------
# ENV setup for testing
# -------------------------------
os.environ["TESTING"] = "1"

from app.db.connection import get_db_url, get_session  # noqa
from app.models.base import Base  # noqa
from app.services.api_key_service import APIKeyService  # noqa
from app.mcp.mcp_main import mcp  # noqa


# -------------------------------
# Helper: ensure _test in DB URL
# -------------------------------
def check_test_db_url():
    db_url = get_db_url()
    err_msg = (
        f"⚠️ The database URL for tests must contain '_test'. Found: {db_url}"
    )
    if "_test" not in db_url:
        raise RuntimeError(err_msg)
    print(f"✅ Using test database URL: {db_url}")


# -------------------------------
# Helper: wait for DB ready
# -------------------------------
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
# Session fixture: truncate tables before each test
# -------------------------------
@pytest.fixture
def session() -> Session:
    check_test_db_url()
    engine = create_engine(get_db_url())
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()

    # Truncate
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
# FastAPI test client with dependency override
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


@pytest.fixture(scope="function")
def api_key_value(session: Session) -> str:
    """Create a global API key for tests"""
    api_key = APIKeyService.create_api_key(session, "Global Test Key")
    return api_key.key


@pytest.fixture
def mock_chroma():
    """
    Fixture to mock chromadb.HttpClient and Chroma store.
    """
    with patch(
        "app.services.chromadb_service.chromadb.HttpClient"
    ) as mock_client, patch(
        "app.services.chromadb_service.Chroma"
    ) as mock_store:
        mock_instance = mock_store.return_value
        mock_collection = mock_instance._collection
        yield {
            "mock_client": mock_client,
            "mock_store": mock_store,
            "mock_instance": mock_instance,
            "mock_collection": mock_collection,
        }


@pytest.fixture
def mock_minio_client():
    with patch(
        "app.services.minio_service.get_minio_client"
    ) as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_minio_class():
    with patch("app.services.minio_service.Minio") as mock_minio_cls:
        yield mock_minio_cls


@pytest.fixture
def mock_openai_embeddings():
    """
    Fixture to mock OpenAIEmbeddings class from langchain_openai.
    Returns the MagicMock instance and the patcher so it can be asserted if
    needed.
    """
    with patch(
        "app.services.embedding_factory.OpenAIEmbeddings"
    ) as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance, mock_class


@pytest.fixture
def patch_kb_route_services():
    """
    patch dependency router.delete_knowledge_base.
    return (mock_minio_client, mock_vector_store, mock_embeddings).
    """
    with patch(
        "app.api.v1.knowledge_base.router.get_minio_client"
    ) as mock_get_minio_client, patch(
        "app.api.v1.knowledge_base.router.ChromaVectorStore"
    ) as mock_chroma_cls, patch(
        "app.api.v1.knowledge_base.router.EmbeddingsFactory.create"
    ) as mock_embeddings_create:

        mock_minio_client = MagicMock()
        mock_vector_store = MagicMock()
        mock_embeddings = MagicMock()

        mock_get_minio_client.return_value = mock_minio_client
        mock_chroma_cls.return_value = mock_vector_store
        mock_embeddings_create.return_value = mock_embeddings

        yield mock_minio_client, mock_vector_store, mock_embeddings


@pytest.fixture
def patch_query_services():
    """
    Patch EmbeddingsFactory.create and ChromaVectorStore for query_vector_kbs.
    Returns (mock_embeddings, mock_vector_store).
    """
    with patch(
        "app.services.kb_query_service.EmbeddingsFactory.create"
    ) as mock_emb, patch(
        "app.services.kb_query_service.ChromaVectorStore"
    ) as mock_store_cls:

        mock_embeddings = MagicMock()
        mock_emb.return_value = mock_embeddings

        mock_vector_store = MagicMock()
        mock_store_cls.return_value = mock_vector_store

        yield mock_embeddings, mock_vector_store


@pytest.fixture
async def mcp_client():
    async with Client(mcp) as client:
        yield client
