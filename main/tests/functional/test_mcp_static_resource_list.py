import pytest

from app.core.config import settings


@pytest.mark.asyncio
@pytest.mark.mcp
class TestMCPStaticResourceLis:
    async def test_static_resource(self, mcp_client):
        resources = await mcp_client.list_resources()

        assert len(resources) > 0
        for r in resources:
            uri = str(r.uri)
            if uri == "resource://server_info":
                assert settings.mcp_server_name in r.name
                assert settings.mcp_server_description in r.description
                assert "resource://server_info" in uri
