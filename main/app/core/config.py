from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    testing: bool = False
    database_url: str

    @field_validator("database_url", mode="before")
    def escape_percent(cls, v: str) -> str:
        return v.replace("%", "%%") if v else v

    class Config:
        env_file = ".env"


settings = Settings()
