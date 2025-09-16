import pytest
import json
import base64

from app.models.knowledge import KnowledgeBase, Document


@pytest.mark.asyncio
@pytest.mark.mcp
class TestQueryKnowledgeBaseFunctional:
    async def test_query_success_functional(
        self, mcp_client, session, patch_mcp_server_vector_store
    ):
        kb = KnowledgeBase(name="Functional KB", description="desc")
        session.add(kb)
        session.commit()

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

        result = await mcp_client.call_tool(
            "query_knowledge_base",
            {
                "query": "hello world",
                "knowledge_base_ids": [kb.id],
                "top_k": 2,
            },
        )

        # --- Debug Print ---
        decoded_str = base64.b64decode(result.data["context"]).decode()
        decoded = json.loads(decoded_str)

        # --- Assertions ---
        assert "context" in result.data
        decoded = json.loads(base64.b64decode(result.data["context"]).decode())
        assert "context" in decoded

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

        print("\n=== RAW MCP RESULT (empty KB) ===", result.data)

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

        print("\n=== RAW MCP RESULT (not found KB) ===", result.data)

        assert result.data["context"] is None
        assert "No active knowledge base found" in result.data["note"]
