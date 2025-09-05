from fastapi import FastAPI
from app.api.routes import router as api_router

app = FastAPI(
    title="Vector Knowledge Base MCP Server",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# REST
app.include_router(api_router, prefix="/api")
