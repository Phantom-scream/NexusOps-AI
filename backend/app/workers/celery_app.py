"""
NexusOps AI — Celery Application
Background task queue configuration
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "nexusops",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.cluster_tasks",
        "app.workers.analysis_tasks",
        "app.workers.telemetry_tasks",
    ],
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task behavior
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,

    # Result TTL
    result_expires=3600,

    # Retry defaults
    task_default_retry_delay=60,
    task_max_retries=3,

    # Queues
    task_routes={
        "app.workers.cluster_tasks.*": {"queue": "cluster"},
        "app.workers.analysis_tasks.*": {"queue": "analysis"},
        "app.workers.telemetry_tasks.*": {"queue": "telemetry"},
    },
    task_default_queue="default",

    # Periodic Tasks (Celery Beat)
    beat_schedule={
        "sync-all-clusters": {
            "task": "app.workers.cluster_tasks.sync_all_active_clusters",
            "schedule": crontab(minute="*/5"),  # Every 5 minutes
        },
        "detect-anomalies": {
            "task": "app.workers.analysis_tasks.detect_anomalies",
            "schedule": crontab(minute="*/10"),  # Every 10 minutes
        },
        "generate-demo-telemetry": {
            "task": "app.workers.telemetry_tasks.generate_demo_telemetry",
            "schedule": crontab(minute="*/15"),  # Every 15 minutes
        },
        "generate-cost-report": {
            "task": "app.workers.analysis_tasks.generate_cost_report",
            "schedule": crontab(hour="*/6"),  # Every 6 hours
        },
    },
)
