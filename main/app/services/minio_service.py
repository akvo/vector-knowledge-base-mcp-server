import logging
import json
from minio import Minio
from minio.error import S3Error
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_minio_client() -> Minio:
    """
    Get a MinIO client instance for internal operations.
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


def set_bucket_public_read_policy(bucket_name: str):
    """
    Set bucket policy to allow public read access.
    This allows accessing objects without presigned URLs.
    """
    client = get_minio_client()

    # Policy to allow public read access
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{bucket_name}/*"],
            }
        ],
    }

    try:
        client.set_bucket_policy(bucket_name, json.dumps(policy))
        logger.info(f"Set public read policy for bucket '{bucket_name}'")
    except Exception as e:
        logger.error(f"Failed to set bucket policy: {e}")
        raise


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
            # Set public read policy
            set_bucket_public_read_policy(bucket_name)
        else:
            logger.info(f"Bucket '{bucket_name}' already exists.")
            # Ensure policy is set
            set_bucket_public_read_policy(bucket_name)
    except S3Error as e:
        logger.error(
            f"MinIO S3Error while accessing bucket '{bucket_name}': {e}"
        )
        raise
    except Exception as e:
        logger.exception(f"Unexpected error initializing MinIO: {e}")
        raise
