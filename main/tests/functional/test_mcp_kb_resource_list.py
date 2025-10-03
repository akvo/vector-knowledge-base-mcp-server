import pytest


@pytest.mark.asyncio
@pytest.mark.mcp
class TestMCPKnowledgeBaseResourceLis:
    async def test_kb_resource(self, mcp_client):
        resources = await mcp_client.list_resources()

        assert len(resources) > 0
        for r in resources:
            uri = str(r.uri)
            if "resource://knowledge_base/" in uri:
                assert "Testing KB" in r.name
                assert "KB Description" in r.description
                assert "resource://knowledge_base/" in str(r.uri)
