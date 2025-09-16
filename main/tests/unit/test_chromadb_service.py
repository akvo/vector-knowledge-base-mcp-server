import pytest
from langchain_core.documents import Document


@pytest.mark.usefixtures("patch_external_services")
class TestChromaVectorStore:
    def test_add_documents(self, patch_external_services):
        vector_store = patch_external_services["mock_vector_store"]
        doc = Document(
            page_content="Hello world", metadata={"title": "greeting"}
        )
        vector_store.add_documents([doc])
        vector_store.add_documents.assert_called_once_with([doc])

    def test_add_embeddings(self, patch_external_services):
        vector_store = patch_external_services["mock_vector_store"]
        vector_store.add_embeddings(
            ids=["id1"],
            embeddings=[[0.1, 0.2]],
            metadatas=[{"title": "doc1"}],
            documents=["Hello"],
        )
        vector_store.add_embeddings.assert_called_once_with(
            ids=["id1"],
            embeddings=[[0.1, 0.2]],
            metadatas=[{"title": "doc1"}],
            documents=["Hello"],
        )

    def test_similarity_search(self, patch_external_services):
        vector_store = patch_external_services["mock_vector_store"]
        vector_store.similarity_search.return_value = [
            Document(page_content="doc1", metadata={"title": "doc1"})
        ]
        results = vector_store.similarity_search("query")
        vector_store.similarity_search.assert_called_once_with("query")
        assert results[0].page_content == "doc1"

    def test_similarity_search_with_score(self, patch_external_services):
        vector_store = patch_external_services["mock_vector_store"]
        vector_store.similarity_search_with_score.return_value = [
            (Document(page_content="doc1", metadata={"title": "doc1"}), 0.1)
        ]
        results = vector_store.similarity_search_with_score("query")
        vector_store.similarity_search_with_score.assert_called_once_with(
            "query"
        )
        doc, score = results[0]
        assert doc.page_content == "doc1"
        assert score == 0.1

    def test_similarity_search_by_vector(self, patch_external_services):
        vector_store = patch_external_services["mock_vector_store"]
        vector_store.similarity_search_by_vector.return_value = {
            "distances": [0.1, 0.2],
            "metadatas": [{"title": "doc1"}, {"title": "doc2"}],
            "documents": ["doc1", "doc2"],
        }
        res = vector_store.similarity_search_by_vector([0.1, 0.2])
        vector_store.similarity_search_by_vector.assert_called_once_with(
            [0.1, 0.2],
        )
        assert "distances" in res
        assert "metadatas" in res

    def test_delete(self, patch_external_services):
        vector_store = patch_external_services["mock_vector_store"]
        vector_store.delete(["id1"])
        vector_store.delete.assert_called_once_with(["id1"])

    def test_delete_collection(self, patch_external_services):
        vector_store = patch_external_services["mock_vector_store"]
        vector_store.delete_collection()
        vector_store.delete_collection.assert_called_once()
