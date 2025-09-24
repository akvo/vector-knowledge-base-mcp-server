import pytest

from app.core.config import settings
from app.services.embedding_factory import EmbeddingsFactory


@pytest.mark.unit
class TestEmbeddingsFactory:
    def test_create_embeddings_with_mock(self, patch_external_services):
        """Test creating OpenAI embeddings with globally patched mock."""
        mock_emb_instance = patch_external_services["mock_embeddings"]

        emb = EmbeddingsFactory.create()

        assert emb is mock_emb_instance

    def test_create_missing_api_key(self, monkeypatch):
        monkeypatch.setattr(settings, "openai_api_key", None)

        from app.services.embedding_factory import EmbeddingsFactory

        with pytest.raises(ValueError, match="OPENAI_API_KEY must be set"):
            EmbeddingsFactory.create()

    def test_create_missing_api_base(self, monkeypatch):
        monkeypatch.setattr(settings, "openai_api_base", None)
        from app.services.embedding_factory import EmbeddingsFactory

        with pytest.raises(ValueError, match="OPENAI_API_BASE must be set"):
            EmbeddingsFactory.create()

    def test_create_missing_model(self, monkeypatch):
        monkeypatch.setattr(settings, "openai_embeddings_model", None)
        from app.services.embedding_factory import EmbeddingsFactory

        with pytest.raises(
            ValueError, match="OPENAI_EMBEDDINGS_MODEL must be set"
        ):
            EmbeddingsFactory.create()
