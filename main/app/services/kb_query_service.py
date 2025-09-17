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
logger.setLevel(logging.INFO)  # or DEBUG for more details


async def query_vector_kbs(
    query: str, knowledge_base_ids: List[int], top_k: int = 10
):
    """
    Query vector knowledge bases and return relevant documents as context.

    Parameters:
    - query: The input query string.
    - knowledge_base_ids: List of knowledge base IDs to query.
    - top_k: Number of top relevant documents to retrieve.

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

        kb = knowledge_bases[-1]
        logger.info("Using knowledge base ID: %d", kb.id)

        documents = (
            db.query(Document)
            .filter(Document.knowledge_base_id == kb.id)
            .all()
        )
        if not documents:
            logger.warning("Knowledge base %d is empty.", kb.id)
            return {
                "context": empty_context,
                "note": f"Knowledge base {kb.id} is empty.",
            }

        logger.info(
            "Found %d documents in DB for knowledge base %d.",
            len(documents),
            kb.id,
        )

        embeddings = EmbeddingsFactory.create()
        logger.info(
            "Embedding model created: %s", embeddings.__class__.__name__
        )

        # Vector store retriever
        vector_store = ChromaVectorStore(
            collection_name=f"kb_{kb.id}",
            embedding_function=embeddings,
        )
        # Number of chunks to retrieve
        retriever = vector_store.as_retriever(search_kwargs={"k": top_k})

        logger.info("Querying vector store for relevant documents (async)...")
        logger.info(
            "Chroma collection '%s' has %d documents",
            kb.id,
            vector_store._store._collection.count(),
        )
        logger.info(
            "Chroma collections available: %s",
            [c.name for c in vector_store._chroma_client.list_collections()],
        )

        retrieved_docs = await retriever.ainvoke(query)

        logger.info(
            "Retrieved %d documents from vector store.", len(retrieved_docs)
        )

        if not retrieved_docs:
            logger.info(
                "No documents matched the query. "
                "Check if the vector store has vectors "
                "and the embeddings match."
            )

        # Encode context
        serializable_context = [
            {"page_content": doc.page_content, "metadata": doc.metadata}
            for doc in retrieved_docs
        ]
        base64_context = base64.b64encode(
            json.dumps({"context": serializable_context}).encode()
        ).decode()

        return {"context": base64_context}

    except Exception as e:
        logger.exception("Error querying knowledge bases: %s", e)
        return {"context": empty_context, "note": f"Error: {str(e)}"}
    finally:
        db.close()
        logger.info("Database session closed.")
