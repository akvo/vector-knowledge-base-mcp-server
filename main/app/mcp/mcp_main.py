from fastmcp import FastMCP

mcp = FastMCP("Vector Knowledge Base MCP Server")


@mcp.resource("resource:/list/sample")
def sample_resource() -> dict:
    """
    Fake resource
    """
    return {
        "uri": "resource://fake/example",
        "name": "Fake Resource",
        "description": "This is a fake static resource",
        "mimeType": "application/json",
        "metadata": {"foo": "bar"},
    }


@mcp.tool("tool:/greeting")
def greeting(name: str) -> dict:
    return {"message": f"Hello, {name}!"}


# Create ASGI app from MCP server
mcp_app = mcp.http_app(path="/mcp")
