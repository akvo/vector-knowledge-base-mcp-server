import json
import base64

from typing import List
from sqlalchemy.orm import Session

from app.db.connection import SessionLocal
from app.models.knowledge import KnowledgeBase, Document
from app.services.chromadb_service import ChromaVectorStore
from app.services.embedding_factory import EmbeddingsFactory


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
    db: Session = SessionLocal()
    try:
        knowledge_bases = (
            db.query(KnowledgeBase)
            .filter(KnowledgeBase.id.in_(knowledge_base_ids))
            .all()
        )
        if not knowledge_bases:
            return {
                "context": None,
                "note": "No active knowledge base found for given IDs.",
            }

        embeddings = EmbeddingsFactory.create()

        # currently only support querying one knowledge base
        kb = knowledge_bases[-1]
        documents = (
            db.query(Document)
            .filter(Document.knowledge_base_id == kb.id)
            .all()
        )
        if not documents:
            return {
                "context": None,
                "note": f"Knowledge base {kb.id} is empty.",
            }

        # Vector store retriever
        vector_store = ChromaVectorStore(
            collection_name=f"kb_{kb.id}",
            embedding_function=embeddings,
        )
        # Number of chunks to retrieve
        retriever = vector_store.as_retriever(search_kwargs={"k": top_k})

        retrieved_docs = await retriever.aget_relevant_documents(query)

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
        return {"context": None, "note": f"Error: {str(e)}"}
    finally:
        db.close()
