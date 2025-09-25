import json
import base64
import logging
from typing import List
from sqlalchemy.orm import Session

from app.db.connection import get_session
from app.models.knowledge import KnowledgeBase, Document
from app.services.chromadb_service import ChromaVectorStore
from app.services.embedding_factory import EmbeddingsFactory

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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

    logger.info("Querying knowledge bases: %s", knowledge_base_ids)
    logger.info("Query string: %s", query)
    logger.info("Top K: %d", top_k)

    try:
        knowledge_bases = (
            db.query(KnowledgeBase)
            .filter(KnowledgeBase.id.in_(knowledge_base_ids))
            .all()
        )
        if not knowledge_bases:
            logger.warning(
                "No active knowledge base found for IDs: %s",
                knowledge_base_ids,
            )
            return {
                "context": empty_context,
                "note": "No active knowledge base found for given IDs.",
            }

        embeddings = EmbeddingsFactory.create()
        logger.info(
            "Embedding model created: %s", embeddings.__class__.__name__
        )

        # Multiple KBs
        all_results = []
        for kb in knowledge_bases:
            logger.info("Checking KB %d - %s", kb.id, kb.name)

            docs_exist = (
                db.query(Document)
                .filter(Document.knowledge_base_id == kb.id)
                .all()
            )
            if not docs_exist:
                logger.warning("KB %d has no documents.", kb.id)
                continue

            # Vector store retriever
            vector_store = ChromaVectorStore(
                collection_name=f"kb_{kb.id}",
                embedding_function=embeddings,
            )

            logger.info(
                "Querying vector store for relevant documents (async)..."
            )
            logger.info(
                "Chroma collection '%s' has %d documents",
                kb.id,
                vector_store._store._collection.count(),
            )

            # Use similarity search with scores
            results = vector_store.similarity_search_with_score(query, k=top_k)
            logger.info("Retrieved %d results from KB %d", len(results), kb.id)

            for doc, score in results:
                doc.metadata["knowledge_base_id"] = kb.id
                all_results.append((doc, score))

        if not all_results:
            return {
                "context": empty_context,
                "note": "No relevant documents found across selected KBs.",
            }

        # Sort globally by score (lower distance = more relevant)
        all_results.sort(key=lambda x: x[1])

        # Trim to global top_k
        top_results = all_results[:top_k]

        serializable_context = [
            {
                "page_content": doc.page_content,
                "metadata": doc.metadata,
                "score": score,
            }
            for doc, score in top_results
        ]

        base64_context = base64.b64encode(
            json.dumps({"context": serializable_context}).encode()
        ).decode()

        return {"context": base64_context}

    except Exception as e:
        logger.exception("Error querying KBs: %s", e)
        return {"context": empty_context, "note": f"Error: {str(e)}"}

    finally:
        db.close()
        logger.info("Database session closed.")
