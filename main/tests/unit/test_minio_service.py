from unittest.mock import patch, MagicMock

from app.services import minio_service
from app.core.config import settings


class TestMinioService:
    @patch("app.services.minio_service.get_minio_client")
    def test_init_minio_bucket_exists(self, mock_get_client):
        # Arrange: mock client to simulate existing bucket
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_get_client.return_value = mock_client

        # Act
        minio_service.init_minio()

        # Assert
        mock_client.bucket_exists.assert_called_once_with(
            settings.minio_bucket_name
        )
        mock_client.make_bucket.assert_not_called()

    @patch("app.services.minio_service.get_minio_client")
    def test_init_minio_bucket_not_exists(self, mock_get_client):
        # Arrange: mock client to simulate non-existing bucket
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = False
        mock_get_client.return_value = mock_client

        # Act
        minio_service.init_minio()

        # Assert
        mock_client.bucket_exists.assert_called_once_with(
            settings.minio_bucket_name
        )
        mock_client.make_bucket.assert_called_once_with(
            settings.minio_bucket_name
        )

    @patch("app.services.minio_service.Minio")
    def test_get_minio_client_called_with_correct_args(self, mock_minio_cls):
        mock_instance = mock_minio_cls.return_value

        client = minio_service.get_minio_client()

        # call minio constructor with correct args
        mock_minio_cls.assert_called_once_with(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False,
        )

        # assert returned client is the mock instance
        assert client is mock_instance
