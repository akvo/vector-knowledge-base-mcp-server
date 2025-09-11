import pytest
import json
import base64

from unittest.mock import AsyncMock
from app.models.knowledge import KnowledgeBase, Document


@pytest.mark.asyncio
class TestQueryKnowledgeBaseFunctional:
    async def test_query_success_functional(
        self, mcp_client, session, patch_query_services
    ):
        """
        Functional test:
        query KB with one document and ensure tool returns encoded context
        """

        _, mock_store = patch_query_services

        # Create KnowledgeBase
        kb = KnowledgeBase(name="Functional KB", description="desc")
        session.add(kb)
        session.commit()

        # Create Document
        doc = Document(
            knowledge_base_id=kb.id,
            file_path="docs/file1.pdf",
            file_name="file1.pdf",
            file_size=100,
            content_type="application/pdf",
            file_hash="hash_123",
        )
        session.add(doc)
        session.commit()

        # Mock retriever with AsyncMock
        mock_retriever = AsyncMock()
        mock_retriever.aget_relevant_documents.return_value = [
            type(
                "Doc",
                (),
                {
                    "page_content": "functional content",
                    "metadata": {"id": doc.id},
                },
            )()
        ]
        mock_store.as_retriever.return_value = mock_retriever

        # run tool via MCP client
        result = await mcp_client.call_tool(
            "query_knowledge_base",
            {
                "query": "hello world",
                "knowledge_base_ids": [kb.id],
                "top_k": 2,
            },
        )

        # verify result
        assert "context" in result.data
        decoded = json.loads(base64.b64decode(result.data["context"]).decode())
        assert decoded["context"][0]["page_content"] == "functional content"
        assert decoded["context"][0]["metadata"]["id"] == doc.id

    async def test_query_empty_kb_functional(self, mcp_client, session):
        """
        Functional test: query KB with no documents should return note
        """
        from app.models.knowledge import KnowledgeBase

        kb = KnowledgeBase(name="Empty KB Func", description="desc")
        session.add(kb)
        session.commit()

        result = await mcp_client.call_tool(
            "query_knowledge_base",
            {
                "query": "nothing here",
                "knowledge_base_ids": [kb.id],
                "top_k": 2,
            },
        )

        assert result.data["context"] is None
        assert f"Knowledge base {kb.id} is empty." in result.data["note"]

    async def test_query_not_found_kb_functional(self, mcp_client):
        """
        Functional test: query with invalid KB ID should return note
        """
        result = await mcp_client.call_tool(
            "query_knowledge_base",
            {
                "query": "ghost query",
                "knowledge_base_ids": [99999],
                "top_k": 2,
            },
        )

        assert result.data["context"] is None
        assert "No active knowledge base found" in result.data["note"]
