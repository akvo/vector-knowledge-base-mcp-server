import logging

from minio import Minio
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_minio_client() -> Minio:
    """
    Get a MinIO client instance.
    """
    logger.info("Creating MinIO client instance.")
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=False,  # Set to True if using HTTPS
    )


def init_minio():
    """
    Initialize MinIO by creating the bucket if it doesn't exist.
    """
    client = get_minio_client()
    logger.info(f"Checking if bucket {settings.minio_bucket_name} exists.")
    if not client.bucket_exists(settings.minio_bucket_name):
        logger.info(f"Bucket {settings.minio_bucket_name} does not exist.")
        logger.info("Creating bucket.")
        client.make_bucket(settings.minio_bucket_name)
    else:
        logger.info(f"Bucket {settings.minio_bucket_name} already exists.")
