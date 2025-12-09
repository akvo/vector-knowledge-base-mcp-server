import pytest

from unittest.mock import MagicMock, patch
from celery.exceptions import MaxRetriesExceededError
from app.tasks.kb_cleanup_task import cleanup_kb_task


@pytest.mark.unit
class TestCleanupKBTask:
    @patch("app.tasks.kb_cleanup_task.get_session")
    @patch("app.tasks.kb_cleanup_task.KnowledgeBaseService")
    def test_cleanup_success(self, mock_service_cls, mock_get_session):
        # Mock DB session
        db_mock = MagicMock()
        mock_get_session.return_value = iter([db_mock])

        # Mock KB service
        service_mock = MagicMock()
        mock_service_cls.return_value = service_mock

        # Patch retry to check it's not called
        retry_mock = MagicMock()
        setattr(cleanup_kb_task, "retry", retry_mock)

        # Run task
        cleanup_kb_task(kb_id=123)

        service_mock.cleanup_kb_resources.assert_called_once_with(123)
        db_mock.close.assert_called_once()
        retry_mock.assert_not_called()

    @patch("app.tasks.kb_cleanup_task.get_session")
    @patch("app.tasks.kb_cleanup_task.KnowledgeBaseService")
    def test_cleanup_retry(self, mock_service_cls, mock_get_session):
        db_mock = MagicMock()
        mock_get_session.return_value = iter([db_mock])

        # Service raises an exception
        service_mock = MagicMock()
        service_mock.cleanup_kb_resources.side_effect = Exception("boom")
        mock_service_cls.return_value = service_mock

        # Patch retry to raise an exception to simulate retry behavior
        retry_mock = MagicMock(side_effect=Exception("RETRY CALLED"))
        setattr(cleanup_kb_task, "retry", retry_mock)

        with pytest.raises(Exception) as exc:  # noqa F841
            cleanup_kb_task(kb_id=456)

        service_mock.cleanup_kb_resources.assert_called_once_with(456)
        db_mock.close.assert_called_once()
        retry_mock.assert_called()

    @patch("app.tasks.kb_cleanup_task.get_session")
    @patch("app.tasks.kb_cleanup_task.KnowledgeBaseService")
    def test_max_retries_exceeded(self, mock_service_cls, mock_get_session):
        db_mock = MagicMock()
        mock_get_session.return_value = iter([db_mock])

        service_mock = MagicMock()
        service_mock.cleanup_kb_resources.side_effect = Exception("boom")
        mock_service_cls.return_value = service_mock

        # Patch retry to raise MaxRetriesExceededError
        retry_mock = MagicMock(side_effect=MaxRetriesExceededError())
        setattr(cleanup_kb_task, "retry", retry_mock)

        with pytest.raises(MaxRetriesExceededError):
            cleanup_kb_task(kb_id=789)

        service_mock.cleanup_kb_resources.assert_called_once_with(789)
        db_mock.close.assert_called_once()
        retry_mock.assert_called()
