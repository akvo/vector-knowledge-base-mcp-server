from celery import shared_task
from datetime import datetime


@shared_task
def heartbeat():
    print(f"[HEARTBEAT] Celery is alive: {datetime.now()}")
    return "OK"
