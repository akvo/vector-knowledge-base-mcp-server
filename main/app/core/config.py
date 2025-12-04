from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    testing: bool = False
    database_url: str

    # PRIVATE MCP CONFIG
    mcp_server_name: str = "Vector Knowledge Base MCP Server"
    mcp_server_description: str = (
        "A secure MCP server that provides access to vector-based knowledge bases. It exposes tools and resources for querying, retrieving, and managing knowledge base documents using similarity search. This server allows LLM-powered agents to discover relevant context across multiple knowledge bases and return grounded responses with supporting evidence."  # noqa
    )

    # MinIO settings
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_name: str = "documents"
    minio_server_url: str = "http://localhost:80/minio"

    # Chroma DB settings
    chroma_db_host: str = "localhost"
    chroma_db_port: int = 8000

    # Vector Store batch processing
    vector_store_batch_size: int = 100

    # OpenAI settings
    openai_api_key: str = "your-openai-api-key-here"
    openai_api_base: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4"
    openai_embeddings_model: str = "text-embedding-ada-002"

    # Admin API Key
    admin_api_key: str = "your-admin-api-key-here"

    @field_validator("database_url", mode="before")
    def escape_percent(cls, v: str) -> str:
        return v.replace("%", "%%") if v else v

    class Config:
        env_file = ".env"


settings = Settings()
