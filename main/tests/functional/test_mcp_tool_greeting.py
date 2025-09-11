import pytest


@pytest.mark.asyncio
class TestMcpToolGreeting:
    async def test_greeting_tool(self, mcp_client):
        result = await mcp_client.call_tool("greeting", {"name": "Alice"})
        assert result.data["message"] == "Hello, Alice!"
