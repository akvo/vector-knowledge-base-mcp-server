import os
import re
import logging
import hashlib
import asyncio

from io import BytesIO
from datetime import datetime, timedelta
from typing import List, Dict
from fastapi import HTTPException, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session, selectinload
from minio.error import MinioException

from app.models.knowledge import (
    KnowledgeBase,
    Document,
    DocumentChunk,
    DocumentUpload,
    ProcessingTask,
)
from app.services.minio_service import (
    get_minio_client,
)
from app.services.embedding_factory import EmbeddingsFactory
from app.services.chromadb_service import ChromaVectorStore
from app.services.document_processor import (
    preview_document,
    process_document_background,
    PreviewResult,
)
from app.services.processing_task_service import ProcessingTaskService
from app.core.config import settings
from app.utils.mime_utils import get_file_info

logger = logging.getLogger(__name__)


def make_clean_filename(filename: str) -> str:
    name, ext = os.path.splitext(filename)
    # Replace ., -, spaces with _
    name = re.sub(r"[.\-\s]", "_", name)
    # Remove everything not alphanumeric or underscore
    name = re.sub(r"[^A-Za-z0-9_]", "", name)
    # Replace multiple underscores with a single one
    name = re.sub(r"_+", "_", name)
    # Remove leading/trailing underscores
    name = name.strip("_")
    return f"{name}{ext.lower()}"


class DocumentService:
    def __init__(self, kb_id: int | None, db: Session):
        self.kb_id = kb_id
        self.db = db

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

            # Get clean filename
            clean_filename = file.filename  # revert, don't use cleanfilename

            existing = (
                self.db.query(Document)
                .filter(
                    Document.file_name == clean_filename,
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
                        "file_size": existing.file_size,
                        "status": "exists",
                        "message": "Document already exists",
                        "skip_processing": True,
                    }
                )
                continue

            # Use clean filename for temp path
            temp_path = f"kb_{self.kb_id}/temp/{clean_filename}"

            try:
                minio_client = get_minio_client()

                # Use BytesIO for upload
                data_stream = BytesIO(file_content)
                content_type = file.content_type or "application/octet-stream"

                logger.info(
                    f"Uploading {clean_filename} to MinIO "
                    f"(size: {len(file_content)} bytes)"
                )

                minio_client.put_object(
                    bucket_name=settings.minio_bucket_name,
                    object_name=temp_path,
                    data=data_stream,
                    length=len(file_content),
                    content_type=content_type,
                )

                # Simple, safe MinIO verification
                verified = False
                max_attempts = 5

                for attempt in range(max_attempts):
                    try:
                        stat = minio_client.stat_object(
                            bucket_name=settings.minio_bucket_name,
                            object_name=temp_path,
                        )

                        if stat.size == len(file_content):
                            logger.info(
                                f"✓ MinIO upload verified: {clean_filename} ({stat.size} bytes)"  # noqa
                            )
                            verified = True
                            break
                        else:
                            logger.warning(
                                f"[Verify] Size mismatch (attempt {attempt+1}/{max_attempts}): "  # noqa
                                f"expected {len(file_content)}, got {stat.size}"  # noqa
                            )

                    except Exception as e:
                        logger.warning(
                            f"[Verify] Attempt {attempt+1}/{max_attempts} failed: {e}"  # noqa
                        )

                    await asyncio.sleep(0.05 * (attempt + 1))

                if not verified:
                    # ❗ Do NOT raise errors and do NOT delete file
                    logger.warning(
                        f"[Verify] MinIO upload not fully verified for {clean_filename}. "  # noqa
                        "Proceeding anyway; downloader will perform its own safety checks."  # noqa
                    )

            except MinioException as e:
                logger.error(
                    f"MinIO upload failed for {clean_filename}: {str(e)}"
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload file {clean_filename}: {str(e)}",
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload file to MinIO: {str(e)}",
                )

            upload = DocumentUpload(
                knowledge_base_id=self.kb_id,
                file_name=clean_filename,
                file_hash=file_hash,
                file_size=len(file_content),
                content_type=content_type,
                temp_path=temp_path,
            )
            self.db.add(upload)
            self.db.commit()
            self.db.refresh(upload)

            results.append(
                {
                    "upload_id": upload.id,
                    "file_name": clean_filename,
                    "temp_path": temp_path,
                    "file_size": len(file_content),
                    "status": "pending",
                    "skip_processing": False,
                }
            )

        return results

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
                "file_size": uploads_dict[t.document_upload_id].file_size,
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
        await asyncio.sleep(0.3)
        for data in task_data:
            asyncio.create_task(
                process_document_background(
                    temp_path=data["temp_path"],
                    file_name=data["file_name"],
                    file_size=data["file_size"],
                    kb_id=self.kb_id,
                    task_id=data["task_id"],
                    db=None,
                )
            )
        logger.info(
            f"Queued {len(task_data)} processing tasks for KB {self.kb_id}"
        )

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
        url = self._build_direct_url(doc.file_path)
        setattr(doc, "file_url", url)
        return doc

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

    def get_documents_upload(self):
        """Return all documents for the given Knowledge Base."""
        kb = self.db.query(KnowledgeBase).filter_by(id=self.kb_id).first()
        if not kb:
            raise HTTPException(
                status_code=404,
                detail="Knowledge base not found",
            )

        docs = (
            self.db.query(DocumentUpload)
            .filter(DocumentUpload.knowledge_base_id == self.kb_id)
            .order_by(DocumentUpload.created_at.desc())
            .all()
        )

        return [
            {
                "id": doc.id,
                "file_name": doc.file_name,
                "status": doc.status,
                "knowledge_base_id": doc.knowledge_base_id,
                "content_type": doc.content_type,
                "created_at": (
                    doc.created_at.isoformat() if doc.created_at else None
                ),
            }
            for doc in docs
        ]

    async def delete_document(self, document_id: int, user=None):
        """
        Delete a document from either `documents` or `document_uploads`,
        along with MinIO and Chroma cleanup.
        """
        doc = (
            self.db.query(Document)
            .filter(
                Document.id == document_id,
                Document.knowledge_base_id == self.kb_id,
            )
            .first()
        )
        upload = None

        # If not found in main table, check uploads
        if not doc:
            upload = (
                self.db.query(DocumentUpload)
                .filter(
                    DocumentUpload.id == document_id,
                    DocumentUpload.knowledge_base_id == self.kb_id,
                )
                .first()
            )
            if not upload:
                raise HTTPException(
                    status_code=404, detail="Document not found"
                )

        # if doc found use file_hash to check the document_uploads record
        if doc and doc.file_hash:
            upload = (
                self.db.query(DocumentUpload)
                .filter(
                    DocumentUpload.file_hash == doc.file_hash,
                    DocumentUpload.knowledge_base_id == self.kb_id,
                )
                .first()
            )

        # Permission validation
        if user and not user.is_admin:
            raise HTTPException(
                status_code=403, detail="Not authorized to delete"
            )

        minio_client = get_minio_client()
        chroma_deleted = False
        minio_deleted = False

        # Delete from Chroma (only for processed)
        if doc:
            try:
                vector_store = ChromaVectorStore(
                    collection_name=f"kb_{self.kb_id}",
                    embedding_function=EmbeddingsFactory.create(),
                )
                vector_store.delete(filter={"document_id": document_id})
                chroma_deleted = True
            except Exception as e:
                logger.warning(
                    f"Chroma delete failed for document {document_id}: {e}"
                )

        # Delete from MinIO
        file_path = doc.file_path if doc else upload.temp_path
        try:
            minio_client.remove_object(settings.minio_bucket_name, file_path)
            minio_deleted = True
            logger.info(f"Deleted object from MinIO: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete from MinIO ({file_path}): {e}")

        # Database Cleanup
        try:
            if doc:
                self.db.query(DocumentChunk).filter_by(
                    document_id=doc.id
                ).delete()
                self.db.delete(doc)
            if upload:
                self.db.delete(upload)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500, detail=f"DB cleanup failed: {e}"
            )

        return {
            "success": True,
            "message": "Document deleted successfully",
            "document_id": document_id,
            "deleted_from": "documents" if doc else "document_uploads",
            "chroma_deleted": chroma_deleted,
            "minio_deleted": minio_deleted,
        }

    def _build_direct_url(self, file_path: str) -> str:
        # Create direct URL through Nginx proxy
        # (no signature needed with public bucket)
        # Format: http://localhost:8080/minio/BUCKET/OBJECT_PATH
        base = f"{settings.minio_server_url}/{settings.minio_bucket_name}"
        url = f"{base}/{file_path}"
        logger.info(f"Generated direct URL: {url}")
        return url

    async def get_presigned_file_info(self, doc_id: int):
        doc = (
            self.db.query(Document)
            .filter(
                Document.id == doc_id,
                Document.knowledge_base_id == self.kb_id,
            )
            .first()
        )
        upload = None
        if not doc:
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
                    status_code=404, detail="Document not found"
                )

        file_name = doc.file_name if doc else upload.file_name
        file_path = doc.file_path if doc else upload.temp_path
        url = self._build_direct_url(file_path)
        file_info = get_file_info(file_name)

        return {
            "document_id": doc_id,
            "file_name": file_name,
            "file_path": file_path,
            "file_type": file_info["mime_type"],
            "file_extension": file_info["file_extension"],
            "file_url": url,
            "is_viewable_in_browser": file_info["is_viewable_in_browser"],
            "source": "documents" if doc else "document_uploads",
        }
