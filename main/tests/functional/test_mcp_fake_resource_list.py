import pytest
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
