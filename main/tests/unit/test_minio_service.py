import pytest

from app.services import minio_service
from app.core.config import settings


@pytest.mark.unit
class TestMinioService:
    def test_init_minio_bucket_exists(self, mock_minio_client):
        # Arrange
        mock_minio_client.bucket_exists.return_value = True

        # Act
        minio_service.init_minio()

        # Assert
        mock_minio_client.bucket_exists.assert_called_once_with(
            settings.minio_bucket_name
        )
        mock_minio_client.make_bucket.assert_not_called()

    def test_init_minio_bucket_not_exists(self, mock_minio_client):
        # Arrange
        mock_minio_client.bucket_exists.return_value = False

        # Act
        minio_service.init_minio()

        # Assert
        mock_minio_client.bucket_exists.assert_called_once_with(
            settings.minio_bucket_name
        )
        mock_minio_client.make_bucket.assert_called_once_with(
            settings.minio_bucket_name
        )

    def test_get_minio_client_called_with_correct_args(self, mock_minio_class):
        # Arrange
        mock_instance = mock_minio_class.return_value

        # Act
        client = minio_service.get_minio_client()

        # Assert
        mock_minio_class.assert_called_once_with(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False,
        )
        assert client is mock_instance
