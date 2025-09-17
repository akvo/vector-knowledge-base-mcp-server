import chromadb

from typing import List, Any, Optional
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_chroma import Chroma
from app.core.config import settings


# TODO :: Implement batch size on add documents function
# take a look into Akvo RAG chroma.py
class ChromaVectorStore:
    def __init__(
        self,
        collection_name: str,
        embedding_function: Optional[Embeddings] = None,
    ):
        """Initialize Chroma vector store."""
        self._chroma_client = chromadb.HttpClient(
            host=settings.chroma_db_host,
            port=settings.chroma_db_port,
        )

        if settings.testing:
            collection_name = f"{collection_name}_test"

        self._store = Chroma(
            client=self._chroma_client,
            collection_name=collection_name,
            embedding_function=embedding_function,
        )

    def add_documents(self, documents: List[Document]) -> None:
        self._store.add_documents(documents)

    def add_embeddings(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[dict]] = None,
        documents: Optional[List[str]] = None,
    ) -> None:
        """
        Add pre-computed embeddings directly.
        This is useful for image embeddings or any custom vector.
        """
        self._store._collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents,
        )

    def delete(self, ids: List[str]) -> None:
        """Delete documents or embeddings by their IDs."""
        self._store.delete(ids)

    def as_retriever(self, **kwargs: Any):
        """Return a retriever interface."""
        return self._store.as_retriever(**kwargs)

    def similarity_search(
        self, query: str, k: int = 4, **kwargs: Any
    ) -> List[Document]:
        """Search for similar documents (text)."""
        return self._store.similarity_search(query, k=k, **kwargs)

    def similarity_search_with_score(
        self, query: str, k: int = 4, **kwargs: Any
    ) -> List[Document]:
        """Search for similar documents with scores."""
        return self._store.similarity_search_with_score(query, k=k, **kwargs)

    def similarity_search_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        include: Optional[List[str]] = None,
    ) -> dict:
        """
        Search for similar items using an embedding vector directly.
        Returns raw query result from Chroma.
        """
        return self._store._collection.query(
            query_embeddings=[embedding],
            n_results=k,
            include=include or ["distances", "metadatas"],
        )

    def delete_collection(self) -> None:
        """Delete the entire collection."""
        self._chroma_client.delete_collection(self._store._collection.name)
