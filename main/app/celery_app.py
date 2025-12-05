from celery import Celery
from app.core.config import settings


CELERY_BROKER_URL = f"amqp://{settings.rabbitmq_user}:{settings.rabbitmq_pass}@{settings.rabbitmq_host}:{settings.rabbitmq_port}//"  # noqa
CELERY_RESULT_BACKEND = "rpc://"

celery_app = Celery(
    "akvo_rag", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Jakarta",
    enable_utc=True,
)

celery_app.autodiscover_tasks(["app.tasks"])
