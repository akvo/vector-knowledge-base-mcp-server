from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    testing: bool = False
    database_url: str

    # MinIO settings
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucker_name: str = "documents"

    # Chroma DB settings
    chroma_db_host: str = "localhost"
    chroma_db_port: int = 8000

    @field_validator("database_url", mode="before")
    def escape_percent(cls, v: str) -> str:
        return v.replace("%", "%%") if v else v

    class Config:
        env_file = ".env"


settings = Settings()
