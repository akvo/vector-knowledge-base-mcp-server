import pytest
import json
import base64
from unittest.mock import AsyncMock
from langchain.schema import Document as LangChainDoc
from app.models.knowledge import KnowledgeBase, Document


@pytest.mark.asyncio
@pytest.mark.mcp
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

        # --- Mock retriever dengan LangChainDoc ---
        mock_doc = LangChainDoc(
            page_content="hello world, functional content",
            metadata={"id": doc.id},
        )

        mock_retriever = AsyncMock()
        mock_retriever.aget_relevant_documents.return_value = [mock_doc]
        mock_store.as_retriever.return_value = mock_retriever

        # tool via MCP client
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

        assert "context" in decoded
        # assert (
        #     decoded["context"][0]["page_content"]
        #     == "hello world, functional content"
        # )
        # assert decoded["context"][0]["metadata"]["id"] == doc.id

    async def test_query_empty_kb_functional(self, mcp_client, session):
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
