import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeBase


@pytest.mark.asyncio
class TestKnowledgeBaseRoutes:
    def get_headers(self, api_key_value: str):
        return {"Authorization": f"API-Key {api_key_value}"}

    async def test_create_kb_requires_api_key(
        self, app: FastAPI, client: AsyncClient
    ):
        """No API key should return 401"""
        res = await client.post(
            app.url_path_for("v1_create_knowledge_base"),
            json={"name": "Test KB", "description": "Desc"},
        )
        assert res.status_code == 401
        assert res.json()["detail"] == "API key required"

    async def test_create_kb_success(
        self, app: FastAPI, client: AsyncClient, api_key_value: str
    ):
        """Create knowledge base successfully"""
        res = await client.post(
            app.url_path_for("v1_create_knowledge_base"),
            headers=self.get_headers(api_key_value),
            json={"name": "Test KB", "description": "Desc"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "Test KB"
        assert "id" in data

    async def test_list_kb(
        self, app: FastAPI, client: AsyncClient, api_key_value: str
    ):
        """List knowledge bases"""
        # Create one first
        res = await client.post(
            app.url_path_for("v1_create_knowledge_base"),
            headers=self.get_headers(api_key_value),
            json={"name": "Test KB", "description": "Desc"},
        )
        assert res.status_code == 200

        # Now list
        res = await client.get(
            app.url_path_for("v1_list_knowledge_bases"),
            headers=self.get_headers(api_key_value),
        )
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_get_kb_and_not_found(
        self,
        app: FastAPI,
        session: Session,
        client: AsyncClient,
        api_key_value: str,
    ):
        """Get knowledge base by ID and handle not found"""
        # Create one first
        res = await client.post(
            app.url_path_for("v1_create_knowledge_base"),
            headers=self.get_headers(api_key_value),
            json={"name": "Test KB", "description": "Desc"},
        )
        assert res.status_code == 200

        kb = session.query(KnowledgeBase).first()

        res = await client.get(
            app.url_path_for("v1_get_knowledge_base", kb_id=kb.id),
            headers=self.get_headers(api_key_value),
        )
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == kb.id

        res = await client.get(
            app.url_path_for("v1_get_knowledge_base", kb_id=999999),
            headers=self.get_headers(api_key_value),
        )
        assert res.status_code == 404
        assert res.json()["detail"] == "Knowledge base not found"

    async def test_update_kb_and_not_found(
        self,
        app: FastAPI,
        session: Session,
        client: AsyncClient,
        api_key_value: str,
    ):
        """Update knowledge base and handle not found"""
        # Create one first
        res = await client.post(
            app.url_path_for("v1_create_knowledge_base"),
            headers=self.get_headers(api_key_value),
            json={"name": "Test KB", "description": "Desc"},
        )
        assert res.status_code == 200

        kb = session.query(KnowledgeBase).first()

        # success update
        res = await client.put(
            app.url_path_for("v1_update_knowledge_base", kb_id=kb.id),
            headers=self.get_headers(api_key_value),
            json={"description": "Updated Desc"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == kb.name
        assert data["description"] == "Updated Desc"

        # not found
        res = await client.put(
            app.url_path_for("v1_update_knowledge_base", kb_id=999999),
            headers=self.get_headers(api_key_value),
            json={"description": "Nope"},
        )
        assert res.status_code == 404
        assert res.json()["detail"] == "Knowledge base not found"
