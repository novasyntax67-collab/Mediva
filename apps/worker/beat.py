import os
from celery_app import celery
from celery.schedules import crontab

# Configurable outbox polling interval (seconds)
OUTBOX_POLL_INTERVAL = int(os.getenv("OUTBOX_POLL_INTERVAL_SECONDS", "5"))

celery.conf.beat_schedule = {
    # ── Outbox Publisher ──────────────────────────────────────────────────
    # Polls event_outbox for pending rows and dispatches to EventBus.
    # Default: every 5 seconds. Configurable via OUTBOX_POLL_INTERVAL_SECONDS.
    "poll-outbox-pending-events": {
        "task": "queues.outbox_publisher.publish_pending_events",
        "schedule": OUTBOX_POLL_INTERVAL,
    },

    # ── Periodic Analytics ────────────────────────────────────────────────
    "run-daily-cleanup-at-midnight": {
        "task": "queues.cleanup.daily_cleanup",
        "schedule": crontab(hour=0, minute=0),
    },
    "run-vitals-analytics-hourly": {
        "task": "queues.analytics.aggregate_vitals",
        "schedule": crontab(minute=0),
    },
}
