import pytest

from app.core.config import settings
from app.services.embedding_factory import EmbeddingsFactory


@pytest.mark.unit
class TestEmbeddingsFactory:
    def test_create_embeddings_with_mock(self, mock_openai_embeddings):
        """Test creating OpenAI embeddings with mocked class."""
        mock_instance, mock_class = mock_openai_embeddings

        emb = EmbeddingsFactory.create()

        mock_class.assert_called_once_with(
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_api_base,
            model=settings.openai_embeddings_model,
        )

        assert emb is mock_instance

    def test_create_missing_api_key(self, monkeypatch, mock_openai_embeddings):
        monkeypatch.setattr(settings, "openai_api_key", None)

        with pytest.raises(ValueError, match="OPENAI_API_KEY must be set"):
            EmbeddingsFactory.create()

    def test_create_missing_api_base(
        self, monkeypatch, mock_openai_embeddings
    ):
        monkeypatch.setattr(settings, "openai_api_base", None)

        with pytest.raises(ValueError, match="OPENAI_API_BASE must be set"):
            EmbeddingsFactory.create()

    def test_create_missing_model(self, monkeypatch, mock_openai_embeddings):
        monkeypatch.setattr(settings, "openai_embeddings_model", None)

        with pytest.raises(
            ValueError, match="OPENAI_EMBEDDINGS_MODEL must be set"
        ):
            EmbeddingsFactory.create()
