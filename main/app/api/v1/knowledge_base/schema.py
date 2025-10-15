from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.schemas.knowledge_schema import (
    KnowledgeBaseBase,
    DocumentBase,
    DocumentUploadBase,
    ProcessingTaskBase,
    PreviewRequest,
)


class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass


class KnowledgeBaseUpdate(KnowledgeBaseBase):
    name: Optional[str] = None


class DocumentCreate(DocumentBase):
    knowledge_base_id: int


class DocumentUploadCreate(DocumentUploadBase):
    knowledge_base_id: int


class DocumentUploadResponse(DocumentUploadBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProcessingTaskCreate(ProcessingTaskBase):
    document_id: int
    knowledge_base_id: int


class ProcessingTask(ProcessingTaskBase):
    id: int
    document_id: int
    knowledge_base_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(DocumentBase):
    id: int
    knowledge_base_id: int
    created_at: datetime
    updated_at: datetime
    processing_tasks: Optional[List[ProcessingTask]] = None

    class Config:
        from_attributes = True


class KnowledgeBaseResponse(KnowledgeBaseBase):
    id: int
    created_at: datetime
    updated_at: datetime
    documents: List[DocumentResponse] = []

    class Config:
        from_attributes = True


class PreviewRequest(PreviewRequest):
    pass


class TestRetrievalRequest(BaseModel):
    query: str
    kb_id: int
    top_k: int


class DocumentUploadItem(BaseModel):
    id: int
    file_name: str
    status: str
    knowledge_base_id: int
    content_type: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True
