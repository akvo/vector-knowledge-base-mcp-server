import time

from fastmcp.server.auth import AuthProvider, AccessToken
from fastapi import HTTPException
from app.services.api_key_service import APIKeyService
from app.db.connection import get_session


class APIKeyAuthProvider(AuthProvider):
    async def authenticate(self, auth_header: str):
        """
        Validate API Key from Authorization header.
        Support:
        - "API-Key <token>"
        - "Bearer API-Key <token>"
        """
        if not auth_header:
            raise HTTPException(401, "Authorization header required")

        # Remove Bearer prefix if exists
        if auth_header.startswith("Bearer "):
            auth_header = auth_header[len("Bearer ") :].strip()  # noqa

        if not auth_header.startswith("API-Key "):
            raise HTTPException(401, "API key required")

        raw_key = auth_header.split(" ", 1)[1]

        # Validate with DB
        db = next(get_session())
        db_key = APIKeyService.get_api_key_by_key(db, raw_key)
        if not db_key or not db_key.is_active:
            raise HTTPException(401, "Invalid or inactive API key")

        # Update last_used
        APIKeyService.update_last_used(db, db_key)

        # Return AccessToken object
        return AccessToken(
            token=raw_key,
            client_id=str(db_key.id),
            metadata={"name": db_key.name},
            issued_at=int(time.time()),
            expires_at=None,
            scopes=[],
        )

    async def verify_token(self, token: str):
        # Strip prefix "API-Key " jika ada
        if token.startswith("API-Key "):
            token = token[len("API-Key ") :].strip()  # noqa

        db = next(get_session())
        db_key = APIKeyService.get_api_key_by_key(db, token)
        if not db_key or not db_key.is_active:
            return None

        return AccessToken(
            token=token,
            client_id=str(db_key.id),
            metadata={"name": db_key.name},
            issued_at=int(time.time()),
            expires_at=None,
            scopes=[],
        )
