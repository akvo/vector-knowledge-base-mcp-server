from typing import List, Optional
from datetime import datetime

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
    processing_tasks: List[ProcessingTask] = []

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
