from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Text,
    DateTime,
    JSON,
    BigInteger,
    TIMESTAMP,
    text,
)
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
from datetime import datetime
import sqlalchemy as sa


class KnowledgeBase(Base, TimestampMixin):
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    documents = relationship(
        "Document",
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
    )
    document_uploads = relationship(
        "DocumentUpload",
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
    )


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String(255), nullable=False)  # Path in MinIO
    file_name = Column(String(255), nullable=False)  # Actual file name
    file_size = Column(BigInteger, nullable=False)  # File size in bytes
    content_type = Column(String(100), nullable=False)  # MIME type
    file_hash = Column(String(64), index=True)  # SHA-256 hash of file content
    knowledge_base_id = Column(
        Integer, ForeignKey("knowledge_bases.id"), nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")

    __table_args__ = (
        # Ensure file_name is unique within each knowledge base
        sa.UniqueConstraint(
            "knowledge_base_id", "file_name", name="uq_kb_file_name"
        ),
    )


class DocumentUpload(Base):
    __tablename__ = "document_uploads"

    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(
        Integer,
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_name = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    content_type = Column(String(100), nullable=False)
    temp_path = Column(String(255), nullable=False)
    created_at = Column(
        TIMESTAMP, nullable=False, server_default=text("now()")
    )
    status = Column(String(50), nullable=False, server_default="pending")
    error_message = Column(Text)

    # Relationships
    knowledge_base = relationship(
        "KnowledgeBase", back_populates="document_uploads"
    )
