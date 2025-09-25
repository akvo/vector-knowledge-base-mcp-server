from typing import List
from app.services.kb_query_service import query_vector_kbs

from app.mcp.secure_mcp import SecureFastMCP
from app.mcp.mcp_auth import APIKeyAuthProvider
from app.mcp.resources.kb_resources import load_kb_resources

# User SecureFastMCP + APIKeyAuthProvider
mcp = SecureFastMCP(
    name="Vector Knowledge Base MCP Server",
    auth=APIKeyAuthProvider(),
)

# Load Dynamic MCP Resources
load_kb_resources(mcp=mcp)


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
