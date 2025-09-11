import pytest

from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeBase


@pytest.mark.asyncio
class TestTestRetrievalRoute:
    def get_headers(self, api_key_value: str):
        return {"Authorization": f"API-Key {api_key_value}"}

    async def test_retrieval_unauthorized(
        self, app: FastAPI, client: AsyncClient
    ):
        """Should return 401 if no API key provided"""
        res = await client.post(
            app.url_path_for("v1_test_retrieval"),
            json={"kb_id": 1, "query": "hello", "top_k": 2},
        )
        assert res.status_code == 401
        assert res.json()["detail"] == "API key required"

    async def test_retrieval_kb_not_found(
        self,
        app: FastAPI,
        client: AsyncClient,
        api_key_value: str,
    ):
        """Should return 404 if KB does not exist"""
        res = await client.post(
            app.url_path_for("v1_test_retrieval"),
            headers=self.get_headers(api_key_value),
            json={"kb_id": 9999, "query": "hello", "top_k": 2},
        )
        assert res.status_code == 404
        assert res.json()["detail"] == "Knowledge base 9999 not found"

    async def test_retrieval_success(
        self,
        app: FastAPI,
        session: Session,
        client: AsyncClient,
        api_key_value: str,
        patch_kb_route_services,
    ):
        """Should return mocked search results"""
        _, mock_vector_store, mock_embeddings, _ = patch_kb_route_services

        kb = KnowledgeBase(name="KB Retrieval", description="desc")
        session.add(kb)
        session.commit()

        mock_vector_store.similarity_search_with_score.return_value = [
            (
                type(
                    "Doc",
                    (),
                    {
                        "page_content": "mock content 1",
                        "metadata": {"source": "file1.txt"},
                    },
                )(),
                0.8,
            ),
            (
                type(
                    "Doc",
                    (),
                    {
                        "page_content": "mock content 2",
                        "metadata": {"source": "file2.txt"},
                    },
                )(),
                0.6,
            ),
        ]

        res = await client.post(
            app.url_path_for("v1_test_retrieval"),
            headers=self.get_headers(api_key_value),
            json={"kb_id": kb.id, "query": "hello", "top_k": 2},
        )

        assert res.status_code == 200
        data = res.json()
        assert "results" in data
        assert len(data["results"]) == 2
        assert data["results"][0]["content"] == "mock content 1"
        assert data["results"][0]["metadata"]["source"] == "file1.txt"
        assert isinstance(data["results"][0]["score"], float)

    async def test_retrieval_internal_error(
        self,
        app: FastAPI,
        session: Session,
        client: AsyncClient,
        api_key_value: str,
        patch_kb_route_services,
    ):
        """Should return 500 if vector store throws error"""
        _, mock_vector_store, _, _ = patch_kb_route_services

        kb = KnowledgeBase(name="KB Retrieval Fail", description="desc")
        session.add(kb)
        session.commit()

        mock_vector_store.similarity_search_with_score.side_effect = Exception(
            "Vector store failed"
        )

        res = await client.post(
            app.url_path_for("v1_test_retrieval"),
            headers=self.get_headers(api_key_value),
            json={"kb_id": kb.id, "query": "failcase", "top_k": 1},
        )

        assert res.status_code == 500
        assert "Vector store failed" in res.json()["detail"]
