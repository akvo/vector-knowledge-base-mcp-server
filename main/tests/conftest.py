import os
import sys
import time
import warnings
import pytest
import pytest_asyncio

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# -------------------------------
# ENV setup for testing
# -------------------------------
os.environ["TESTING"] = "1"

from app.db.connection import get_db_url, get_session
from app.models.base import Base
from app.services.api_key_service import APIKeyService


# -------------------------------
# Helper: ensure _test in DB URL
# -------------------------------
def check_test_db_url():
    db_url = get_db_url()
    if "_test" not in db_url:
        raise RuntimeError(
            f"⚠️ The database URL for tests must contain '_test'. Found: {db_url}"
        )
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
