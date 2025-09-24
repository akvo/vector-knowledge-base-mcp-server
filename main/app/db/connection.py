from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


def get_db_url():
    url = settings.database_url
    if settings.testing and not url.endswith("_test"):
        url += "_test"
    return url


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
