import os
import sys
from celery import Celery

# Add backend-core to path for events/models imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "packages", "backend-core")))

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery = Celery(
    "mediva-worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "queues.outbox_publisher",
        "queues.notification",
        "queues.analytics",
        "queues.reminder",
        "queues.risk_worker",
        "queues.ai_worker",
        "queues.cleanup",
        "queues.emails",
    ]
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
