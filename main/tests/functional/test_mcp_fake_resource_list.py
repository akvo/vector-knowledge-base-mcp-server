import pytest
import json

from fastmcp import Client
from app.mcp.mcp_main import mcp


@pytest.mark.asyncio
async def test_sample_resource():
    async with Client(mcp) as client:
        resources = await client.list_resources()

        target = next(
            (r for r in resources if str(r.uri) == "resource:/list/sample"),
            None,
        )
        assert target is not None

        content = await client.read_resource(target.uri)
        res = json.loads(content[0].text)

        assert res["uri"] == "resource://fake/example"
        assert res["name"] == "Fake Resource"
        assert res["mimeType"] == "application/json"
        assert res["metadata"]["foo"] == "bar"
