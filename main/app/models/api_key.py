import secrets

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    VARCHAR,
)
from app.models.base import Base, TimestampMixin


class APIKey(Base, TimestampMixin):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(VARCHAR(128), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    @staticmethod
    def generate_api_key(length: int = 32) -> str:
        return secrets.token_hex(length)

    def mark_used(self):
        self.last_used = datetime.utcnow()
