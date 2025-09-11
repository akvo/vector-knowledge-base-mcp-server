import pytest
import json


@pytest.mark.asyncio
class TestMCPResourceListSample:
    async def test_sample_resource(self, mcp_client):
        resources = await mcp_client.list_resources()

        target = next(
            (r for r in resources if str(r.uri) == "resource:/list/sample"),
            None,
        )
        assert target is not None

        content = await mcp_client.read_resource(target.uri)
        res = json.loads(content[0].text)

        assert res["uri"] == "resource://fake/example"
        assert res["name"] == "Fake Resource"
        assert res["mimeType"] == "application/json"
        assert res["metadata"]["foo"] == "bar"
