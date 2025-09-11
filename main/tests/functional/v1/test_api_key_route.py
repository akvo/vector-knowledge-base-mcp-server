import pytest

from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.core.config import settings


@pytest.mark.asyncio
class TestAPIKeyRoute:
    def get_admin_headers(self):
        """Return headers with valid Admin-Key"""
        return {"Authorization": f"Admin-Key {settings.admin_api_key}"}

    async def test_create_api_key(
        self, app: FastAPI, session: Session, client: AsyncClient
    ):
        """Create API key route should create and return the key"""
        response = await client.post(
            app.url_path_for("v1_create_api_key"),
            json={"name": "Test Key"},
        )
        assert response.status_code == 401

        response = await client.post(
            app.url_path_for("v1_create_api_key"),
            headers=self.get_admin_headers(),
            json={"name": "Test Key"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Key"

    async def test_list_api_keys(
        self, app: FastAPI, session: Session, client: AsyncClient
    ):
        """List API keys route should return multiple keys"""
        res = await client.post(
            app.url_path_for("v1_create_api_key"),
            json={"name": "List Key"},
        )
        res.status_code == 401

        await client.post(
            app.url_path_for("v1_create_api_key"),
            headers=self.get_admin_headers(),
            json={"name": "List Key"},
        )
        response = await client.get(
            app.url_path_for("v1_list_api_keys"),
            headers=self.get_admin_headers(),
        )
        assert response.status_code == 200
        keys = response.json()
        assert any(k["name"] == "List Key" for k in keys)

    async def test_update_api_key(
        self, app: FastAPI, session: Session, client: AsyncClient
    ):
        """Update API key route should modify key attributes"""
        res = await client.put(
            app.url_path_for("v1_update_api_key", id=100),
            json={"is_active": False},
        )
        assert res.status_code == 401

        # Return 404
        response = await client.put(
            app.url_path_for("v1_update_api_key", id=100),
            headers=self.get_admin_headers(),
            json={"is_active": False},
        )
        assert response.status_code == 404

        # Create first
        resp = await client.post(
            app.url_path_for("v1_create_api_key"),
            headers=self.get_admin_headers(),
            json={"name": "To Update"},
        )
        api_key_id = resp.json()["id"]

        # Update
        response = await client.put(
            app.url_path_for("v1_update_api_key", id=api_key_id),
            headers=self.get_admin_headers(),
            json={"is_active": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    async def test_delete_api_key(
        self, app: FastAPI, session: Session, client: AsyncClient
    ):
        """Delete API key route should remove the key"""
        res = await client.delete(
            app.url_path_for("v1_delete_api_key", id=100),
        )
        assert res.status_code == 401

        # Return 404
        response = await client.delete(
            app.url_path_for("v1_delete_api_key", id=100),
            headers=self.get_admin_headers(),
        )
        assert response.status_code == 404

        # Create first
        resp = await client.post(
            app.url_path_for("v1_create_api_key"),
            headers=self.get_admin_headers(),
            json={"name": "To Delete"},
        )
        api_key_id = resp.json()["id"]

        # Delete
        response = await client.delete(
            app.url_path_for("v1_delete_api_key", id=api_key_id),
            headers=self.get_admin_headers(),
        )
        assert response.status_code == 200

        response = await client.get(
            app.url_path_for("v1_list_api_keys"),
            headers=self.get_admin_headers(),
        )
        keys = response.json()
        assert not any(k["id"] == api_key_id for k in keys)
