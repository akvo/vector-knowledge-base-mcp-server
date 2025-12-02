import os
import logging
import hashlib
import tempfile
import traceback
import uuid
import asyncio

from io import BytesIO
from typing import Optional, List, Dict
from fastapi import UploadFile
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader,
    TextLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangchainDocument
from pydantic import BaseModel
from sqlalchemy.orm import Session
from minio.error import MinioException
from minio.commonconfig import CopySource

from app.db.connection import get_session
from app.core.config import settings
from app.services.minio_service import get_minio_client
from app.models.knowledge import Document, DocumentChunk
from app.services.chunk_record import ChunkRecord
from app.services.chromadb_service import ChromaVectorStore
from app.services.embedding_factory import EmbeddingsFactory
from app.services.processing_task_service import ProcessingTaskService


class UploadResult(BaseModel):
    file_path: str
    file_name: str
    file_size: int
    content_type: str
    file_hash: str


class TextChunk(BaseModel):
    content: str
    metadata: Optional[Dict] = None


class PreviewResult(BaseModel):
    chunks: List[TextChunk]
    total_chunks: int


def generate_chunk_id(
    kb_id: int, file_name: str, chunk_content: str, chunk_metadata: dict
) -> tuple[str, str]:
    """
    Generate consistent chunk ID and hash for document chunks.

    Args:
        kb_id: Knowledge base ID
        file_name: Name of the source file
        chunk_content: The text content of the chunk
        chunk_metadata: Metadata dictionary for the chunk

    Returns:
        tuple: (chunk_hash, chunk_id) - hash of content+metadata,
        and unique chunk ID
    """
    # Generate content hash including metadata for uniqueness
    chunk_hash = hashlib.sha256(
        (chunk_content + str(chunk_metadata)).encode()
    ).hexdigest()

    # Generate unique chunk ID using knowledge base, filename, and content hash
    chunk_id = hashlib.sha256(
        f"{kb_id}:{file_name}:{chunk_hash}".encode()
    ).hexdigest()

    return chunk_hash, chunk_id


async def process_document(
    file_path: str,
    file_name: str,
    kb_id: int,
    document_id: int,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> None:
    """
    Process document and store in vector database with incremental updates
    """
    logger = logging.getLogger(__name__)

    try:
        preview_result = await preview_document(
            file_path, chunk_size, chunk_overlap
        )

        # Initialize embeddings
        logger.info("Initializing OpenAI embeddings...")
        embeddings = EmbeddingsFactory.create()

        logger.info(f"Initializing vector store with collection: kb_{kb_id}")
        vector_store = ChromaVectorStore(
            collection_name=f"kb_{kb_id}",
            embedding_function=embeddings,
        )

        # Initialize chunk record manager
        chunk_manager = ChunkRecord(kb_id)

        # Get existing chunk hashes for this file
        existing_hashes = chunk_manager.list_chunks(file_name)

        # Prepare new chunks
        new_chunks = []
        current_hashes = set()
        documents_to_update = []

        for chunk in preview_result.chunks:
            # Generate consistent chunk hash and ID
            chunk_hash, chunk_id = generate_chunk_id(
                kb_id=kb_id,
                file_name=file_name,
                chunk_content=chunk.content,
                chunk_metadata=chunk.metadata,
            )
            current_hashes.add(chunk_hash)

            # Skip if chunk hasn't changed
            if chunk_hash in existing_hashes:
                continue

            # Prepare chunk record
            # Prepare metadata
            metadata = {
                **chunk.metadata,
                "chunk_id": chunk_id,
                "file_name": file_name,
                "kb_id": kb_id,
                "document_id": document_id,
            }

            new_chunks.append(
                {
                    "id": chunk_id,
                    "kb_id": kb_id,
                    "document_id": document_id,
                    "file_name": file_name,
                    "metadata": metadata,
                    "hash": chunk_hash,
                }
            )

            # Prepare document for vector store
            doc = LangchainDocument(
                page_content=chunk.content, metadata=metadata
            )
            documents_to_update.append(doc)

        # Add new chunks to database and vector store
        if new_chunks:
            logger.info(f"Adding {len(new_chunks)} new/updated chunks")
            chunk_manager.add_chunks(new_chunks)
            vector_store.add_documents(documents_to_update)

        # Delete removed chunks
        chunks_to_delete = chunk_manager.get_deleted_chunks(
            current_hashes, file_name
        )
        if chunks_to_delete:
            logger.info(f"Removing {len(chunks_to_delete)} deleted chunks")
            chunk_manager.delete_chunks(chunks_to_delete)
            vector_store.delete(chunks_to_delete)

        logger.info("Document processing completed successfully")

    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise


async def upload_document(file: UploadFile, kb_id: int) -> UploadResult:
    """Step 1: Upload document to MinIO"""
    content = await file.read()
    file_size = len(content)

    file_hash = hashlib.sha256(content).hexdigest()

    # Clean and normalize filename
    file_name = "".join(
        c for c in file.filename if c.isalnum() or c in ("-", "_", ".")
    ).strip()
    object_path = f"kb_{kb_id}/{file_name}"

    docx = "application/vnd.openxmlformats"
    docx += ".officedocument.wordprocessingml.document"

    content_types = {
        ".pdf": "application/pdf",
        ".docx": docx,
        ".md": "text/markdown",
        ".txt": "text/plain",
    }

    _, ext = os.path.splitext(file_name)
    content_type = content_types.get(ext.lower(), "application/octet-stream")

    # Upload to MinIO
    minio_client = get_minio_client()
    try:
        minio_client.put_object(
            bucket_name=settings.minio_bucket_name,
            object_name=object_path,
            data=BytesIO(content),
            length=file_size,
            content_type=content_type,
        )
    except Exception as e:
        logging.error(f"Failed to upload file to MinIO: {str(e)}")
        raise

    return UploadResult(
        file_path=object_path,
        file_name=file_name,
        file_size=file_size,
        content_type=content_type,
        file_hash=file_hash,
    )


async def preview_document(
    file_path: str, chunk_size: int = 1000, chunk_overlap: int = 200
) -> PreviewResult:
    """Step 2: Generate preview chunks"""
    # Get file from MinIO
    minio_client = get_minio_client()
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    # Download to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
        minio_client.fget_object(
            bucket_name=settings.minio_bucket_name,
            object_name=file_path,
            file_path=temp_file.name,
        )
        temp_path = temp_file.name

    try:
        # Select appropriate loader
        if ext == ".pdf":
            loader = PyPDFLoader(temp_path)
        elif ext == ".docx":
            loader = Docx2txtLoader(temp_path)
        elif ext == ".md":
            loader = UnstructuredMarkdownLoader(temp_path)
        else:  # Default to text loader
            loader = TextLoader(temp_path)

        # Load and split the document
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        chunks = text_splitter.split_documents(documents)

        # Convert to preview format
        preview_chunks = [
            TextChunk(content=chunk.page_content, metadata=chunk.metadata)
            for chunk in chunks
        ]

        return PreviewResult(chunks=preview_chunks, total_chunks=len(chunks))
    finally:
        os.unlink(temp_path)


async def process_document_background(
    temp_path: str,
    file_name: str,
    kb_id: int,
    task_id: int,
    db: Session = None,
    file_size: int = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> None:
    """Process document in background"""
    logger = logging.getLogger(__name__)
    logger.info(
        f"Starting background processing for task {task_id}, file: {file_name}"
    )

    # if we don't pass in db, create a new database session
    if db is None:
        db = next(get_session())
        should_close_db = True
    else:
        should_close_db = False

    task_service = ProcessingTaskService(db)
    task = task_service.get_task(task_id)
    if not task:
        logger.error(f"Task {task_id} not found")
        return

    try:
        logger.info(f"Task {task_id}: Setting status to processing")
        task.status = "processing"
        db.commit()

        # 1. Ensure temp file exists in MinIO and download it
        minio_client = get_minio_client()

        # --- MinIO write stabilization ---
        try:
            await asyncio.sleep(0.2)
            for _ in range(3):
                stat = minio_client.stat_object(
                    settings.minio_bucket_name, temp_path
                )
                # only enforce size check if expected_size exists
                if file_size is None and stat.size >= file_size:
                    break
                await asyncio.sleep(0.2)
        except Exception:
            # Do NOT fail task here — only fail if fget_object also fails
            pass
        # --- end stabilization ---

        try:
            local_temp_path = f"/tmp/{task_id}_{uuid.uuid4().hex}_{file_name}"

            download_msg = f"Downloading file from MinIO: {temp_path}"
            download_msg += f" to local path: {local_temp_path}"

            logger.info(f"Task {task_id}: {download_msg}")

            minio_client.fget_object(
                bucket_name=settings.minio_bucket_name,
                object_name=temp_path,
                file_path=local_temp_path,
            )
            logger.info(f"Task {task_id}: File downloaded successfully")
        except MinioException as e:
            error_msg = f"Failed to download temp file: {str(e)}"
            logger.error(f"Task {task_id}: {error_msg}")
            raise Exception(error_msg)

        try:
            # 2. Load and split document
            _, ext = os.path.splitext(file_name)
            ext = ext.lower()

            logger.info(
                f"Task {task_id}: Loading document with extension {ext}"
            )
            # Select appropriate loader
            if ext == ".pdf":
                loader = PyPDFLoader(local_temp_path)
            elif ext == ".docx":
                loader = Docx2txtLoader(local_temp_path)
            elif ext == ".md":
                loader = UnstructuredMarkdownLoader(local_temp_path)
            else:  # Default to text loader
                loader = TextLoader(local_temp_path)

            logger.info(f"Task {task_id}: Loading document content")
            documents = loader.load()
            logger.info(f"Task {task_id}: Document loaded successfully")

            logger.info(f"Task {task_id}: Splitting document into chunks")
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )
            chunks = text_splitter.split_documents(documents)
            logger.info(
                f"Task {task_id}: Document split into {len(chunks)} chunks"
            )

            # 3. Initialize vector store
            logger.info(f"Task {task_id}: Initializing vector store")
            embeddings = EmbeddingsFactory.create()

            vector_store = ChromaVectorStore(
                collection_name=f"kb_{kb_id}",
                embedding_function=embeddings,
            )

            # 4. Move file to permanent storage in MinIO
            permanent_path = f"kb_{kb_id}/{file_name}"
            try:
                logger.info(
                    f"Task {task_id}: Moving file to permanent storage"
                )
                # Use copy and delete to simulate move
                source = CopySource(settings.minio_bucket_name, temp_path)
                minio_client.copy_object(
                    bucket_name=settings.minio_bucket_name,
                    object_name=permanent_path,
                    source=source,
                )
                logger.info(f"Task {task_id}: File moved to permanent storage")

                # Delete temp file from MinIO
                logger.info(
                    f"Task {task_id}: Removing temporary file from MinIO"
                )
                minio_client.remove_object(
                    bucket_name=settings.minio_bucket_name,
                    object_name=temp_path,
                )
                logger.info(f"Task {task_id}: Temporary file removed")
            except MinioException as e:
                error_msg = (
                    f"Failed to move file to permanent storage: {str(e)}"
                )
                logger.error(f"Task {task_id}: {error_msg}")
                raise Exception(error_msg)

            # 5. Create document record in DB
            logger.info(f"Task {task_id}: Creating document record")
            document = Document(
                file_name=file_name,
                file_path=permanent_path,
                file_hash=task.document_upload.file_hash,
                file_size=task.document_upload.file_size,
                content_type=task.document_upload.content_type,
                knowledge_base_id=kb_id,
            )
            db.add(document)
            db.commit()
            db.refresh(document)
            logger.info(
                f"Task {task_id}: Document record created ID {document.id}"
            )

            # 6. Store chunks with incremental update
            logger.info(f"Task {task_id}: Storing document chunks")
            for i, chunk in enumerate(chunks):
                # Generate consistent chunk hash and ID using shared function
                chunk_hash, chunk_id = generate_chunk_id(
                    kb_id=kb_id,
                    file_name=file_name,
                    chunk_content=chunk.page_content,
                    chunk_metadata=chunk.metadata,
                )

                chunk.metadata["source"] = file_name
                chunk.metadata["kb_id"] = kb_id
                chunk.metadata["document_id"] = document.id
                chunk.metadata["chunk_id"] = chunk_id

                doc_chunk = DocumentChunk(
                    id=chunk_id,  # Use generated chunk ID
                    document_id=document.id,
                    kb_id=kb_id,
                    file_name=file_name,
                    chunk_metadata={
                        "page_content": chunk.page_content,
                        **chunk.metadata,
                    },
                    hash=hashlib.sha256(
                        (chunk.page_content + str(chunk.metadata)).encode()
                    ).hexdigest(),
                )
                db.add(doc_chunk)
                if i > 0 and i % 100 == 0:
                    logger.info(f"Task {task_id}: Stored {i} chunks")
                    db.commit()  # Commit every 100 chunks

            # 7. Add chunks to vector store
            logger.info(
                f"Task {task_id}: Adding {len(chunks)} chunks to vector store"
            )
            vector_store.add_documents(chunks)

            msg = f"All {len(chunks)} chunks added to vector store"
            logger.info(f"Task {task_id}: {msg}")

            # 8. Update task status to completed
            logger.info(f"Task {task_id}: Updating task status to completed")
            task.status = "completed"
            task.document_id = document.id  # Link processed document

            # 9. Update document upload status if applicable
            upload = task.document_upload  # Should be preloaded
            if upload:
                msg = "Updating upload record status to completed"
                logger.info(f"Task {task_id}: {msg}")
                upload.status = "completed"

            db.commit()
            logger.info(f"Task {task_id}: Processing completed successfully")

        finally:
            # Clean up local temp file
            try:
                if os.path.exists(local_temp_path):
                    logger.info(f"Task {task_id}: Cleaning up local temp file")
                    os.remove(local_temp_path)
                    logger.info(f"Task {task_id}: Local temp file cleaned up")
            except Exception as e:
                msg = f"Failed to clean up local temp file: {str(e)}"
                logger.warning(f"Task {task_id}: {msg}")

    except Exception as e:
        logger.error(f"Task {task_id}: Error processing document: {str(e)}")
        logger.error(f"Task {task_id}: Stack trace: {traceback.format_exc()}")
        task.status = "failed"
        task.error_message = str(e)
        db.commit()

        # Clean up temp file in MinIO if it still exists
        try:
            logger.info(
                f"Task {task_id}: Cleaning up temporary file after error"
            )
            minio_client.remove_object(
                bucket_name=settings.minio_bucket_name, object_name=temp_path
            )
            logger.info(
                f"Task {task_id}: Temporary file cleaned up after error"
            )
        except Exception as e:
            logger.warning(
                f"Task {task_id}: Failed to clean up temporary file: {e}"
            )
    finally:
        # if we create the db session, we need to close it
        if should_close_db and db:
            db.close()
