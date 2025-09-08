from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


def get_db_url():
    TESTING = settings.testing
    DATABASE_URL = settings.database_url
    DB_URL = f"{DATABASE_URL}_test" if TESTING else DATABASE_URL
    return DB_URL


def get_engine():
    return create_engine(get_db_url(), pool_size=1, max_overflow=20)


SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=get_engine()
)


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
