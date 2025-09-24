from typing import List
from app.services.kb_query_service import query_vector_kbs

from app.mcp.secure_mcp import SecureFastMCP
from app.mcp.mcp_auth import APIKeyAuthProvider


# User SecureFastMCP + APIKeyAuthProvider
mcp = SecureFastMCP(
    name="Vector Knowledge Base MCP Server",
    auth=APIKeyAuthProvider(),
)


@mcp.resource(
    uri="resource:/list/sample",
    name="Sample Resource",
    description="A sample static resource",
    mime_type="application/json",
)
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


@mcp.tool(name="greeting", description="Greet a person with their name.")
def greeting(name: str) -> dict:
    return {"message": f"Hello, {name}!"}


@mcp.tool(
    name="query_knowledge_base",
    description="Query a specific knowledge base return answer with context.",
)
async def query_knowledge_base(
    query: str, knowledge_base_ids: List[int], top_k: int = 10
):
    return await query_vector_kbs(
        query=query, knowledge_base_ids=knowledge_base_ids, top_k=top_k
    )


# Create ASGI app from SecureMCP
mcp_app = mcp.http_app(path="/")
