import logging

from fastmcp.resources import TextResource

from app.db.connection import SessionLocal
from app.models.knowledge import KnowledgeBase
from app.core.config import settings


logger = logging.getLogger(__name__)


def load_kb_resources(mcp):
    """
    Register KBs as resources with their description included
    in resource metadata.
    """
    logger.info("🔄 Loading Knowledge Base resources...")
    if settings.testing:
        for i in range(2):
            resource = TextResource(
                uri=f"resource://knowledge_base/{i}",
                name=f"Testing KB {i}",
                text="",
                description="KB Description",
                tags={"knowledge-base"},
            )
            mcp.add_resource(resource)
        return

    try:
        session = SessionLocal()
        kb_list = session.query(KnowledgeBase).all()

        if not kb_list:
            logger.info("ℹ️ No Knowledge Bases found to load.")
            return

        base_uri = "resource://knowledge_base"
        for kb in kb_list:
            resource = TextResource(
                uri=f"{base_uri}/{kb.id}",
                name=kb.name,
                text="",
                description=kb.description or "",
                tags={"knowledge-base"},
            )
            mcp.add_resource(resource)

        logger.info(f"✅ Loaded {len(kb_list)} KB resources into MCP.")

    except Exception as e:
        logger.error(
            f"❌ Error while loading KB resources: {e}", exc_info=True
        )
    finally:
        session.close()
