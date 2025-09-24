from app.core.config import settings
from langchain_openai import OpenAIEmbeddings


class EmbeddingsFactory:
    @staticmethod
    def create():
        """
        Factory method to create an embedding instance based on .env config.
        Validates required configuration values.
        """
        api_key = settings.openai_api_key
        api_base = settings.openai_api_base
        model = settings.openai_embeddings_model

        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set")
        if not api_base:
            raise ValueError("OPENAI_API_BASE must be set")
        if not model:
            raise ValueError("OPENAI_EMBEDDINGS_MODEL must be set")

        return OpenAIEmbeddings(
            openai_api_key=api_key,
            openai_api_base=api_base,
            model=model,
        )
