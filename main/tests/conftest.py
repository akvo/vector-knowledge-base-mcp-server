import os
import sys
import pytest
import warnings
import pytest_asyncio

from alembic import command
from alembic.config import Config
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)


# Apply migrations at beginning and end of testing session
@pytest.fixture(scope="session")
def apply_migrations():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    os.environ["TESTING"] = "1"
    config = Config("alembic.ini")
    command.upgrade(config, "head")


@pytest.fixture
def app() -> FastAPI:
    from app.main import app

    return app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncClient:
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            yield client
