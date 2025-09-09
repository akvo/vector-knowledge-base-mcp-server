import logging

from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.routes import router as api_router
from app.mcp.mcp_main import mcp_app
from app.services.minio_service import init_minio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


# Main lifespan function to handle startup and shutdown events
@asynccontextmanager
async def app_lifespan(app: FastAPI):
    logging.info("Starting up the app...")
    init_minio()
    yield
    logging.info("Shutting down the app...")


# Combine multiple lifespan functions if needed
@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    async with app_lifespan(app):
        async with mcp_app.lifespan(app):
            yield


app = FastAPI(
    title="Vector Knowledge Base API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=combined_lifespan,
)


# REST API (Include routers)
app.include_router(api_router, prefix="/api")

# Mount the MCP server
app.mount("/", mcp_app)
