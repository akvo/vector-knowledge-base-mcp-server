import logging

from fastmcp.resources import TextResource

from app.core.config import settings


logger = logging.getLogger(__name__)


def get_server_info(mcp):
    """
    Generate dynamic text content describing the MCP server.
    Called every time the resource is read.
    """
    resource = TextResource(
        uri="resource://server_info",
        name=settings.mcp_server_name,
        text="",
        description=settings.mcp_server_description,
        tags={"server", "info", "knowledge-base"},
    )
    mcp.add_resource(resource)
    logger.info(
        "✅ Registered server info resource for Vector Knowledge Base MCP."
    )
