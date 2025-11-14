import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeBase, Document


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

    async def test_list_kb_without_documents(
        self,
        app: FastAPI,
        client: AsyncClient,
        api_key_value: str,
        session: Session,
    ):
        # --- Insert KB directly ---
        kb = KnowledgeBase(name="KB Docs", description="With docs")
        session.add(kb)
        session.commit()
        session.refresh(kb)

        # --- Insert document directly ---
        doc = Document(
            file_path="/tmp/doc1.txt",
            file_name="doc1.txt",
            file_hash="doc1-hash",
            file_size=10,
            content_type="text/plain",
            knowledge_base_id=kb.id,
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)

        # Now list with_documents=false
        res = await client.get(
            app.url_path_for("v1_list_knowledge_bases"),
            headers=self.get_headers(api_key_value),
            params={"with_documents": False},
        )
        assert res.status_code == 200

        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Validate documents not loaded
        first = next((x for x in data if x["id"] == kb.id), None)
        assert first is not None
        assert first["documents"] == []  # not loaded

    async def test_list_kb_with_documents(
        self,
        app: FastAPI,
        client: AsyncClient,
        api_key_value: str,
        session: Session,
    ):
        # Create KB directly
        kb = KnowledgeBase(name="KB Docs 2", description="Test")
        session.add(kb)
        session.commit()
        session.refresh(kb)

        # Add doc directly
        doc = Document(
            file_path="/tmp/doc2.txt",
            file_name="doc2.txt",
            file_hash="doc2-hash",
            file_size=10,
            content_type="text/plain",
            knowledge_base_id=kb.id,
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)

        # Call list
        res = await client.get(
            app.url_path_for("v1_list_knowledge_bases"),
            headers=self.get_headers(api_key_value),
            params={"with_documents": True},
        )
        assert res.status_code == 200

        data = res.json()
        found = next((x for x in data if x["id"] == kb.id), None)
        assert found is not None
        assert len(found["documents"]) == 1

    async def test_list_kb_with_total(
        self,
        app: FastAPI,
        client: AsyncClient,
        api_key_value: str,
        session: Session,
    ):
        # seed 1 KB
        kb = KnowledgeBase(name="WithTotalKB", description="Test")
        session.add(kb)
        session.commit()
        session.refresh(kb)

        res = await client.get(
            app.url_path_for("v1_list_knowledge_bases"),
            headers=self.get_headers(api_key_value),
            params={"include_total": True},
        )
        assert res.status_code == 200

        data = res.json()
        assert isinstance(data, dict)
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)

    async def test_list_kb_without_total(
        self,
        app: FastAPI,
        client: AsyncClient,
        api_key_value: str,
        session: Session,
    ):
        # seed 1 KB
        kb = KnowledgeBase(name="WithoutTotalKB", description="Test")
        session.add(kb)
        session.commit()
        session.refresh(kb)

        res = await client.get(
            app.url_path_for("v1_list_knowledge_bases"),
            headers=self.get_headers(api_key_value),
            params={"include_total": False},
        )
        assert res.status_code == 200

        data = res.json()
        assert isinstance(data, list)

    async def test_list_kb_search(
        self,
        app: FastAPI,
        client: AsyncClient,
        api_key_value: str,
        session: Session,
    ):
        # Create a KB with unique name
        kb = KnowledgeBase(name="SearchMeXYZ", description="Test search")
        session.add(kb)
        session.commit()
        session.refresh(kb)

        # Search
        res = await client.get(
            app.url_path_for("v1_list_knowledge_bases"),
            headers=self.get_headers(api_key_value),
            params={"search": "XYZ"},
        )
        assert res.status_code == 200

        data = res.json()
        assert any(item["name"] == "SearchMeXYZ" for item in data)

    async def test_list_kb_pagination(
        self,
        app: FastAPI,
        client: AsyncClient,
        api_key_value: str,
        session: Session,
    ):
        # Ensure at least 3 KBs exist with direct insert
        for i in range(3):
            kb = KnowledgeBase(name=f"PageKB{i}", description="pagination")
            session.add(kb)
        session.commit()

        res = await client.get(
            app.url_path_for("v1_list_knowledge_bases"),
            headers=self.get_headers(api_key_value),
            params={"skip": 1, "limit": 1, "include_total": False},
        )
        assert res.status_code == 200

        data = res.json()
        assert isinstance(data, list)
        assert len(data) == 1  # exact page

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
