from typing import Optional, List
from pydantic import BaseModel


class KnowledgeBaseBase(BaseModel):
    name: str
    description: Optional[str] = None


class DocumentBase(BaseModel):
    file_name: str
    file_path: str
    file_hash: str
    file_size: int
    content_type: str


class DocumentUploadBase(BaseModel):
    file_name: str
    file_hash: str
    file_size: int
    content_type: str
    temp_path: str
    status: str = "pending"
    error_message: Optional[str] = None


class ProcessingTaskBase(BaseModel):
    status: str
    error_message: Optional[str] = None


class PreviewRequest(BaseModel):
    document_ids: List[int]
    chunk_size: int = 1000
    chunk_overlap: int = 200
