import pytest
from app.core.config import settings
from app.services import minio_service


@pytest.mark.unit
class TestMinioService:
    def test_init_minio_bucket_exists(self, patch_external_services):
        mock_minio = patch_external_services["mock_minio"]
        mock_minio.bucket_exists.return_value = True

        minio_service.get_minio_client = lambda: mock_minio

        minio_service.init_minio()

        mock_minio.bucket_exists.assert_called_once_with(
            settings.minio_bucket_name
        )
        mock_minio.make_bucket.assert_not_called()

    def test_init_minio_bucket_not_exists(self, patch_external_services):
        mock_minio = patch_external_services["mock_minio"]
        mock_minio.bucket_exists.return_value = False

        minio_service.get_minio_client = lambda: mock_minio

        minio_service.init_minio()

        mock_minio.bucket_exists.assert_called_once_with(
            settings.minio_bucket_name
        )
        mock_minio.make_bucket.assert_called_once_with(
            settings.minio_bucket_name
        )

    def test_get_minio_client_called_with_correct_args(
        self, patch_external_services
    ):
        mock_minio = patch_external_services["mock_minio"]

        # Patch the Minio class constructor
        from app.services import minio_service as ms

        ms.Minio = lambda endpoint, access_key, secret_key, secure: mock_minio

        client = minio_service.get_minio_client()

        assert client is mock_minio
