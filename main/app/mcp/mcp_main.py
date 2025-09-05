from fastmcp import FastMCP

mcp = FastMCP("Vector Knowledge Base MCP Server")


@mcp.tool
def greeting(name: str) -> dict:
    return {"message": f"Hello, {name}!"}


# Create ASGI app from MCP server
mcp_app = mcp.http_app(path="/mcp")
