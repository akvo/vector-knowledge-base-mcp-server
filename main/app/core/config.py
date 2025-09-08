import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    testing: bool = os.getenv("TESTING", "False").lower() == "true"
    database_url: str = str(os.getenv("DATABASE_URL")).replace("%", "%%")


settings = Settings()
