import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document

from app.services.chromadb_service import ChromaVectorStore


@pytest.mark.unit
class TestChromaVectorStore:
    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        with patch(
            "app.services.chromadb_service.chromadb.HttpClient"
        ) as mock_client, patch(
            "app.services.chromadb_service.Chroma"
        ) as mock_store:
            self.mock_client = mock_client
            self.mock_store = mock_store
            self.mock_instance = mock_store.return_value
            self.mock_collection = self.mock_instance._collection
            yield

    def test_add_documents(self):
        store = ChromaVectorStore("test_collection")
        doc = Document(page_content="hello world", metadata={"id": 1})

        store.add_documents([doc])

        self.mock_instance.add_documents.assert_called_once_with([doc])

    def test_add_embeddings(self):
        store = ChromaVectorStore("test_collection")
        ids = ["1"]
        embeddings = [[0.1, 0.2, 0.3]]
        metadatas = [{"label": "test"}]
        documents = ["hello"]

        store.add_embeddings(
            ids, embeddings, metadatas=metadatas, documents=documents
        )

        self.mock_collection.add.assert_called_once_with(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents,
        )

    def test_delete(self):
        store = ChromaVectorStore("test_collection")
        store.delete(["1"])

        self.mock_instance.delete.assert_called_once_with(["1"])

    def test_similarity_search(self):
        self.mock_instance.similarity_search.return_value = ["fake_result"]

        store = ChromaVectorStore("test_collection")
        result = store.similarity_search("hello")

        self.mock_instance.similarity_search.assert_called_once_with(
            "hello", k=4
        )
        assert result == ["fake_result"]

    def test_similarity_search_with_score(self):
        sim_mock = self.mock_instance.similarity_search_with_score
        sim_mock.return_value = [
            ("doc1", 0.1),
            ("doc2", 0.2),
        ]

        store = ChromaVectorStore("test_collection")
        result = store.similarity_search_with_score("hello", k=2)

        sim_mock.assert_called_once_with("hello", k=2)
        assert isinstance(result, list)
        assert result[0][0] == "doc1"
        assert result[0][1] == 0.1

    def test_similarity_search_by_vector(self):
        self.mock_collection.query.return_value = {
            "ids": ["1"],
            "distances": [0.1],
        }

        store = ChromaVectorStore("test_collection")
        result = store.similarity_search_by_vector([0.1, 0.2, 0.3])

        self.mock_collection.query.assert_called_once()
        assert "ids" in result
        assert result["ids"] == ["1"]

    def test_as_retriever(self):
        mock_retriever = MagicMock()
        self.mock_instance.as_retriever.return_value = mock_retriever

        store = ChromaVectorStore("test_collection")
        retriever = store.as_retriever(search_type="similarity")

        self.mock_instance.as_retriever.assert_called_once_with(
            search_type="similarity"
        )
        assert retriever is mock_retriever

    def test_delete_collection(self):
        mock_client_instance = self.mock_client.return_value

        store = ChromaVectorStore("test_collection")
        store.delete_collection()

        mock_client_instance.delete_collection.assert_called_once_with(
            self.mock_instance._collection.name
        )
