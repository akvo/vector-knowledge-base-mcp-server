import pytest

from unittest.mock import MagicMock
from langchain_core.documents import Document

from app.services.chromadb_service import ChromaVectorStore


@pytest.mark.unit
class TestChromaVectorStore:
    def test_add_documents(self, mock_chroma, mocker):
        store = ChromaVectorStore("test_collection")

        doc1 = Document(page_content="hello world", metadata={"id": 1})
        doc2 = Document(page_content="foo bar", metadata={"id": 2})

        # Force batching to size 1 so we can test the loop
        mocker.patch(
            "app.services.chromadb_service.settings.vector_store_batch_size", 1
        )

        store.add_documents([doc1, doc2])

        # Called once per batch (2 docs -> 2 batches)
        assert mock_chroma["mock_instance"].add_documents.call_count == 2
        mock_chroma["mock_instance"].add_documents.assert_any_call([doc1])
        mock_chroma["mock_instance"].add_documents.assert_any_call([doc2])

    def test_add_embeddings(self, mock_chroma):
        store = ChromaVectorStore("test_collection")
        ids = ["1"]
        embeddings = [[0.1, 0.2, 0.3]]
        metadatas = [{"label": "test"}]
        documents = ["hello"]

        store.add_embeddings(
            ids, embeddings, metadatas=metadatas, documents=documents
        )

        mock_chroma["mock_collection"].add.assert_called_once_with(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents,
        )

    def test_delete(self, mock_chroma):
        store = ChromaVectorStore("test_collection")
        store.delete(["1"])

        mock_chroma["mock_instance"].delete.assert_called_once_with(["1"])

    def test_similarity_search(self, mock_chroma):
        mock_chroma["mock_instance"].similarity_search.return_value = [
            "fake_result"
        ]

        store = ChromaVectorStore("test_collection")
        result = store.similarity_search("hello")

        mock_chroma["mock_instance"].similarity_search.assert_called_once_with(
            "hello", k=4
        )
        assert result == ["fake_result"]

    def test_similarity_search_with_score(self, mock_chroma):
        sim_mock = mock_chroma["mock_instance"].similarity_search_with_score
        sim_mock.return_value = [("doc1", 0.1), ("doc2", 0.2)]

        store = ChromaVectorStore("test_collection")
        result = store.similarity_search_with_score("hello", k=2)

        sim_mock.assert_called_once_with("hello", k=2)
        assert isinstance(result, list)
        assert result[0][0] == "doc1"
        assert result[0][1] == 0.1

    def test_similarity_search_by_vector(self, mock_chroma):
        mock_chroma["mock_collection"].query.return_value = {
            "ids": ["1"],
            "distances": [0.1],
        }

        store = ChromaVectorStore("test_collection")
        result = store.similarity_search_by_vector([0.1, 0.2, 0.3])

        mock_chroma["mock_collection"].query.assert_called_once()
        assert "ids" in result
        assert result["ids"] == ["1"]

    def test_as_retriever(self, mock_chroma):
        mock_retriever = MagicMock()
        mock_chroma["mock_instance"].as_retriever.return_value = mock_retriever

        store = ChromaVectorStore("test_collection")
        retriever = store.as_retriever(search_type="similarity")

        mock_chroma["mock_instance"].as_retriever.assert_called_once_with(
            search_type="similarity"
        )
        assert retriever is mock_retriever

    def test_delete_collection(self, mock_chroma):
        store = ChromaVectorStore("test_collection")
        store.delete_collection()

        mock_chroma[
            "mock_client"
        ].return_value.delete_collection.assert_called_once_with(
            mock_chroma["mock_instance"]._collection.name
        )
