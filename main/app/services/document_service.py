import logging
import hashlib
import asyncio

from datetime import datetime, timedelta
from typing import List, Dict
from fastapi import HTTPException, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session, selectinload
from minio.error import MinioException

from app.models.knowledge import (
    KnowledgeBase,
    Document,
    DocumentUpload,
    ProcessingTask,
)
from app.services.minio_service import get_minio_client
from app.services.embedding_factory import EmbeddingsFactory
from app.services.chromadb_service import ChromaVectorStore
from app.services.document_processor import (
    preview_document,
    process_document_background,
    PreviewResult,
)
from app.services.processing_task_service import ProcessingTaskService
from app.core.config import settings

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, kb_id: int | None, db: Session):
        self.kb_id = kb_id
        self.db = db

    # -----------------------
    # Upload
    # -----------------------
    async def upload_documents(self, files: List[UploadFile]):
        kb = (
            self.db.query(KnowledgeBase)
            .filter(KnowledgeBase.id == self.kb_id)
            .first()
        )
        if not kb:
            raise HTTPException(
                status_code=404, detail="Knowledge base not found"
            )

        results = []
        for file in files:
            file_content = await file.read()
            file_hash = hashlib.sha256(file_content).hexdigest()

            existing = (
                self.db.query(Document)
                .filter(
                    Document.file_name == file.filename,
                    Document.file_hash == file_hash,
                    Document.knowledge_base_id == self.kb_id,
                )
                .first()
            )
            if existing:
                results.append(
                    {
                        "document_id": existing.id,
                        "file_name": existing.file_name,
                        "status": "exists",
                        "message": "Document already exists",
                        "skip_processing": True,
                    }
                )
                continue

            temp_path = f"kb_{self.kb_id}/temp/{file.filename}"
            await file.seek(0)
            try:
                minio_client = get_minio_client()
                minio_client.put_object(
                    bucket_name=settings.minio_bucket_name,
                    object_name=temp_path,
                    data=file.file,
                    length=len(file_content),
                    content_type=file.content_type,
                )
            except MinioException as e:
                logger.error(f"MinIO upload failed: {str(e)}")
                raise HTTPException(
                    status_code=500, detail="Failed to upload file"
                )

            upload = DocumentUpload(
                knowledge_base_id=self.kb_id,
                file_name=file.filename,
                file_hash=file_hash,
                file_size=len(file_content),
                content_type=file.content_type,
                temp_path=temp_path,
            )
            self.db.add(upload)
            self.db.commit()
            self.db.refresh(upload)

            results.append(
                {
                    "upload_id": upload.id,
                    "file_name": file.filename,
                    "temp_path": temp_path,
                    "status": "pending",
                    "skip_processing": False,
                }
            )

        return results

    # -----------------------
    # Preview
    # -----------------------
    async def preview_documents(
        self, preview_request
    ) -> Dict[int, PreviewResult]:
        results = {}
        for doc_id in preview_request.document_ids:
            document = (
                self.db.query(Document)
                .filter(
                    Document.id == doc_id,
                    Document.knowledge_base_id == self.kb_id,
                )
                .first()
            )
            if document:
                file_path = document.file_path
            else:
                upload = (
                    self.db.query(DocumentUpload)
                    .filter(
                        DocumentUpload.id == doc_id,
                        DocumentUpload.knowledge_base_id == self.kb_id,
                    )
                    .first()
                )
                if not upload:
                    raise HTTPException(
                        status_code=404, detail=f"Document {doc_id} not found"
                    )
                file_path = upload.temp_path

            preview = await preview_document(
                file_path,
                chunk_size=preview_request.chunk_size,
                chunk_overlap=preview_request.chunk_overlap,
            )
            results[doc_id] = preview

        return results

    # -----------------------
    # Processing
    # -----------------------
    async def process_documents(
        self, upload_results: List[dict], background_tasks: BackgroundTasks
    ):
        kb = (
            self.db.query(KnowledgeBase)
            .filter(KnowledgeBase.id == self.kb_id)
            .first()
        )
        if not kb:
            raise HTTPException(
                status_code=404, detail="Knowledge base not found"
            )

        task_service = ProcessingTaskService(self.db)

        upload_ids = [
            r["upload_id"]
            for r in upload_results
            if not r.get("skip_processing")
        ]
        if not upload_ids:
            return {"tasks": []}

        uploads = (
            self.db.query(DocumentUpload)
            .filter(DocumentUpload.id.in_(upload_ids))
            .all()
        )
        uploads_dict = {u.id: u for u in uploads}

        tasks = []
        for uid in upload_ids:
            if uid in uploads_dict:
                task = task_service.create_task(self.kb_id, uid)
                tasks.append(task)

        # enqueue background processing
        task_data = [
            {
                "task_id": t.id,
                "upload_id": t.document_upload_id,
                "temp_path": uploads_dict[t.document_upload_id].temp_path,
                "file_name": uploads_dict[t.document_upload_id].file_name,
            }
            for t in tasks
        ]
        background_tasks.add_task(self._enqueue_processing, task_data)

        return {
            "tasks": [
                {"upload_id": t.document_upload_id, "task_id": t.id}
                for t in tasks
            ]
        }

    async def _enqueue_processing(self, task_data: List[dict]):
        for data in task_data:
            asyncio.create_task(
                process_document_background(
                    data["temp_path"],
                    data["file_name"],
                    self.kb_id,
                    data["task_id"],
                    None,
                )
            )
        logger.info(
            f"Queued {len(task_data)} processing tasks for KB {self.kb_id}"
        )

    # -----------------------
    # Cleanup
    # -----------------------
    async def cleanup_temp_files(self):
        expired_time = datetime.utcnow() - timedelta(hours=24)
        expired_uploads = (
            self.db.query(DocumentUpload)
            .filter(DocumentUpload.created_at < expired_time)
            .all()
        )

        minio_client = get_minio_client()
        for upload in expired_uploads:
            try:
                minio_client.remove_object(
                    settings.minio_bucket_name, upload.temp_path
                )
            except MinioException as e:
                logger.error(f"Failed to delete {upload.temp_path}: {str(e)}")
            self.db.delete(upload)
        self.db.commit()

        return {"message": f"Cleaned {len(expired_uploads)} expired uploads"}

    # -----------------------
    # Tasks
    # -----------------------
    async def get_processing_tasks(self, task_ids: str):
        ids = [int(i.strip()) for i in task_ids.split(",")]
        kb = (
            self.db.query(KnowledgeBase)
            .filter(KnowledgeBase.id == self.kb_id)
            .first()
        )
        if not kb:
            raise HTTPException(
                status_code=404, detail="Knowledge base not found"
            )

        tasks = (
            self.db.query(ProcessingTask)
            .options(selectinload(ProcessingTask.document_upload))
            .filter(
                ProcessingTask.id.in_(ids),
                ProcessingTask.knowledge_base_id == self.kb_id,
            )
            .all()
        )

        return {
            t.id: {
                "document_id": t.document_id,
                "status": t.status,
                "error_message": t.error_message,
                "upload_id": t.document_upload_id,
                "file_name": (
                    t.document_upload.file_name if t.document_upload else None
                ),
            }
            for t in tasks
        }

    # -----------------------
    # Get Document
    # -----------------------
    async def get_document(self, doc_id: int):
        doc = (
            self.db.query(Document)
            .filter(
                Document.id == doc_id, Document.knowledge_base_id == self.kb_id
            )
            .first()
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc

    # -----------------------
    # Retrieval
    # -----------------------
    def search(self, query: str, top_k: int = 5):
        embeddings = EmbeddingsFactory.create()
        vector_store = ChromaVectorStore(
            collection_name=f"kb_{self.kb_id}", embedding_function=embeddings
        )
        try:
            results = vector_store.similarity_search_with_score(query, k=top_k)
        except Exception as e:
            logger.error(f"Search failed for KB {self.kb_id}: {e}")
            raise HTTPException(status_code=500, detail="Vector store failed")

        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score),
            }
            for doc, score in results
        ]
