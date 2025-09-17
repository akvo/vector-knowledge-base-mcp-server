from fastapi import FastAPI
from app.api.routes import router as api_router
from app.mcp.mcp_main import mcp_app

app = FastAPI(
    title="Vector Knowledge Base API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=mcp_app.lifespan,  # Key: Pass lifespan to FastAPI
)

# REST API
app.include_router(api_router, prefix="/api")

# Mount the MCP server
app.mount("/", mcp_app)
