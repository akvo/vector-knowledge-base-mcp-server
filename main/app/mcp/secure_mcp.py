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
            # Ensure long-lived MCP streams don’t get closed by ALB or Ingress
            response.headers["Connection"] = "keep-alive"
            response.headers["Keep-Alive"] = "timeout=86400, max=100000"
            response.headers["Cache-Control"] = "no-store"
            response.headers["X-MCP-Stream"] = "true"
            return response

        # --- Simulate 400 error ---
        """
        # For testing retry logic in clients. Fails the first request
        # uncomment to enable.
        @app.middleware("http")
        async def test_bad_request_injector(request: Request, call_next):
            # Initialize a counter on the app instance if not exists
            if not hasattr(app.state, "failure_count"):
                app.state.failure_count = 0

            # Fail the first request only
            if app.state.failure_count < 1:
                app.state.failure_count += 1
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    status_code=400,
                    content={"detail": "Simulated 400 error (1st time only)"},
                )

            return await call_next(request)
        """
        # --- EOL Simulate 400 error ---

        return app
