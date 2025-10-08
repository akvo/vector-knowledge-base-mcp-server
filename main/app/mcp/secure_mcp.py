import logging

from fastmcp import FastMCP
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class SecureFastMCP(FastMCP):
    def http_app(self, path: str = "/mcp") -> FastAPI:
        app = super().http_app(path=path)

        # --- Middleware Auth ---
        @app.middleware("http")
        async def auth_middleware(request: Request, call_next):
            # Only for mcp path
            if request.url.path.startswith(path):
                auth_header = request.headers.get("Authorization")
                if not auth_header:
                    auth_header = request.headers.get("authorization")
                if not auth_header:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Authorization header required"},
                    )
                if self.auth:
                    try:
                        await self.auth.authenticate(auth_header)
                    except Exception as e:
                        logger.error(f"MCP Auth failed: {e}")
                        return JSONResponse(
                            status_code=401,
                            content={"detail": "Invalid or inactive API key"},
                        )
            return await call_next(request)

        # --- Keep-Alive Middleware ---
        @app.middleware("http")
        async def keep_alive_middleware(request: Request, call_next):
            response = await call_next(request)
            response.headers["Connection"] = "keep-alive"
            response.headers["Keep-Alive"] = "timeout=3600, max=10000"
            response.headers["Cache-Control"] = "no-store"
            return response

        return app
