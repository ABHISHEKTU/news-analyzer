# app/core/celery_app.py
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "news_analyzer",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.pipeline"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600,
    task_track_started=True,
    beat_schedule={
        "scan-every-30-minutes": {
            "task": "app.tasks.pipeline.run_pipeline_task",
            "schedule": 1800.0,
        },
    },
)