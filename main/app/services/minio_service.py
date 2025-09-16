import logging

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_minio_client() -> Minio:
    """
    Get a MinIO client instance (force path-style).
    """
    logger.info("Creating MinIO client instance.")

    endpoint = settings.minio_endpoint.replace("http://", "").replace(
        "https://", ""
    )

    client = Minio(
        endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=False,
    )
    return client


def init_minio():
    """
    Initialize MinIO by creating the bucket if it doesn't exist.
    """
    client = get_minio_client()
    bucket_name = settings.minio_bucket_name

    try:
        logger.info(f"Checking if bucket '{bucket_name}' exists...")
        if not client.bucket_exists(bucket_name):
            logger.info(f"Bucket '{bucket_name}' does not exist. Creating...")
            client.make_bucket(bucket_name)
        else:
            logger.info(f"Bucket '{bucket_name}' already exists.")
    except S3Error as e:
        logger.error(
            f"MinIO S3Error while accessing bucket '{bucket_name}': "
            f"MinIO S3Error: {e},"
        )
        raise
    except Exception as e:
        logger.exception(f"Unexpected error initializing MinIO: {e}")
        raise
