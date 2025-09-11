import pytest
from fastmcp import Client
from app.mcp.mcp_main import mcp


@pytest.mark.asyncio
async def test_greeting_tool():
    async with Client(mcp) as client:
        result = await client.call_tool("greeting", {"name": "Alice"})
        assert result.data["message"] == "Hello, Alice!"
