import json
import base64
import logging
import time
import asyncio

from typing import List
from sqlalchemy.orm import Session
from asyncio.exceptions import TimeoutError

from app.db.connection import get_session
from app.models.knowledge import KnowledgeBase, Document
from app.services.chromadb_service import ChromaVectorStore
from app.services.embedding_factory import EmbeddingsFactory

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_cached_embeddings = None


def get_embeddings():
    global _cached_embeddings
    if _cached_embeddings is None:
        _cached_embeddings = EmbeddingsFactory.create()
        logger.info(
            "✅ Embeddings model initialized and cached: %s",
            _cached_embeddings.__class__.__name__,
        )
    return _cached_embeddings


async def safe_similarity_search(
    vector_store, query: str, k: int, timeout: int = 30
):
    """Run Chroma similarity search in a threadpool with timeout handling."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(
                vector_store.similarity_search_with_score, query, k
            ),
            timeout=timeout,
        )
    except TimeoutError:
        logger.warning("⚠️ Chroma search timed out after %s seconds", timeout)
        return []
    except Exception as e:
        logger.error("❌ Chroma search failed: %s", e, exc_info=True)
        return []


# ---- 🩺 Heartbeat coroutine ----
async def heartbeat_task(interval: int = 10):
    """
    Periodically logs to keep connection active.
    Useful behind NAT or idle connection layers.
    """
    try:
        while True:
            logger.debug("💓 [Keepalive] MCP query still running...")
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logger.debug("🫧 [Keepalive] Stopped.")
        raise


# ---- Main MCP Tool Function ----
async def query_vector_kbs(
    query: str, knowledge_base_ids: List[int], top_k: int = 10
):
    """
    Query multiple vector knowledge bases and return globally ranked
    relevant documents.

    Parameters:
    - query: The input query string.
    - knowledge_base_ids: List of knowledge base IDs to query.
    - top_k: Number of top relevant documents (global).

    Returns:
    - dict with base64 encoded context or error note.
    """
    db: Session = next(get_session())

    empty_context = base64.b64encode(
        json.dumps({"context": []}).encode()
    ).decode()
    start_time = time.time()
    logger.info(
        "🧠 [MCP] Querying KBs %s | Query='%s' | top_k=%d",
        knowledge_base_ids,
        query,
        top_k,
    )

    # Start heartbeat
    heartbeat = asyncio.create_task(heartbeat_task(10))  # every 10s
    try:
        # ---- Load KBs ----
        knowledge_bases = (
            db.query(KnowledgeBase)
            .filter(KnowledgeBase.id.in_(knowledge_base_ids))
            .all()
        )
        if not knowledge_bases:
            note = (
                f"No active knowledge base found for IDs: {knowledge_base_ids}"
            )
            logger.warning(note)
            return {"context": empty_context, "note": note}

        embeddings = get_embeddings()
        all_results = []

        # ---- Process each KB ----
        for kb in knowledge_bases:
            kb_start = time.time()
            logger.info("🔍 [KB %d] Checking KB: %s", kb.id, kb.name)

            docs_exist = (
                db.query(Document)
                .filter(Document.knowledge_base_id == kb.id)
                .first()
            )
            if not docs_exist:
                logger.warning("⚠️ Skip [KB %d] No documents found", kb.id)
                continue

            # Vector store retriever
            vector_store = ChromaVectorStore(
                collection_name=f"kb_{kb.id}",
                embedding_function=embeddings,
            )

            try:
                doc_count = vector_store._store._collection.count()
                logger.info(
                    "📚 [KB %d] Collection loaded with %d docs",
                    kb.id,
                    doc_count,
                )
            except Exception:
                logger.warning("⚠️ [KB %d] Could not count docs", kb.id)
                doc_count = 0

            results = await safe_similarity_search(
                vector_store, query, k=top_k, timeout=60
            )
            logger.info(
                "✅ [KB %d] Retrieved %d results in %.2fs",
                kb.id,
                len(results),
                time.time() - kb_start,
            )

            for doc, score in results:
                doc.metadata["knowledge_base_id"] = kb.id
                all_results.append((doc, score))

        # ---- Aggregate results ----
        if not all_results:
            note = "No relevant documents found across selected KBs."
            return {"context": empty_context, "note": note}

        all_results.sort(key=lambda x: x[1])
        top_results = all_results[:top_k]

        serializable_context = [
            {
                "page_content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score),
            }
            for doc, score in top_results
        ]

        base64_context = base64.b64encode(
            json.dumps({"context": serializable_context}).encode()
        ).decode()

        total_time = time.time() - start_time
        logger.info(
            "✅ [MCP] Query completed in %.2fs, returning %d results",
            total_time,
            len(top_results),
        )

        return {
            "context": base64_context,
            "note": f"Query finished in {total_time:.2f}s",
        }

    except Exception as e:
        logger.exception("💥 [MCP] Error querying KBs: %s", e)
        return {"context": empty_context, "note": f"Error: {str(e)}"}

    finally:
        # Stop heartbeat and close DB
        heartbeat.cancel()
        try:
            await heartbeat
        except asyncio.CancelledError:
            pass
        db.close()
        logger.debug("🧹 Database session closed.")
