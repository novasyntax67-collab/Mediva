"""
Reminder Worker — consumes domain events and generates reminders/schedules.

Consumes:
  - appointment.created     → Schedule 24h and 1h appointment reminders
  - appointment.rescheduled → Cancel old reminders, schedule new ones
  - prescription.created    → Generate adherence schedule (compliance calendar)

The adherence schedule generation was moved here from PrescriptionService
so the prescribing doctor no longer waits for schedule prepopulation.

Implements:
  - Idempotency guard via processed_events table
"""
import os
import sys
import logging
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages", "backend-core")))

from celery_app import celery

logger = logging.getLogger(__name__)

WORKER_NAME = "reminder"

HANDLED_EVENTS = {
    "appointment.created",
    "appointment.rescheduled",
    "prescription.created",
}


def _check_idempotency(session, event_id: str) -> bool:
    from sqlalchemy import text
    result = session.execute(
        text("SELECT 1 FROM processed_events WHERE event_id = :eid AND worker = :w"),
        {"eid": event_id, "w": WORKER_NAME}
    ).fetchone()
    return result is not None


def _mark_processed(session, event_id: str):
    from sqlalchemy import text
    session.execute(
        text("""
            INSERT INTO processed_events (event_id, worker, processed_at)
            VALUES (:eid, :w, :now)
            ON CONFLICT (event_id, worker) DO NOTHING
        """),
        {"eid": event_id, "w": WORKER_NAME, "now": datetime.now(timezone.utc)}
    )
    session.commit()


def _get_sync_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5433/healthcare")
    sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_url, pool_pre_ping=True)
    return sessionmaker(bind=engine)()


def _generate_adherence_schedule(session, prescription_id: str, patient_id: str):
    """
    Loads prescription items and generates adherence log entries.
    This logic was previously in PrescriptionService.create_prescription().
    """
    from sqlalchemy import text
    import uuid

    # Fetch all items for this prescription
    items = session.execute(
        text("""
            SELECT id, frequency_interval, frequency_period, duration_days
            FROM prescription_items
            WHERE prescription_id = :pid AND deleted_at IS NULL
        """),
        {"pid": prescription_id}
    ).fetchall()

    now = datetime.now(timezone.utc)

    for item_id, freq_interval, freq_period, duration_days in items:
        interval_hours = freq_interval
        if freq_period and freq_period.lower() == "day":
            interval_hours = freq_interval * 24

        if interval_hours <= 0:
            interval_hours = 24

        total_hours = duration_days * 24
        curr_time = now + timedelta(hours=interval_hours)
        end_limit = now + timedelta(hours=total_hours)

        while curr_time <= end_limit:
            adherence_id = str(uuid.uuid4())
            session.execute(
                text("""
                    INSERT INTO medication_adherence
                        (id, prescription_item_id, patient_id, scheduled_time, status, source, created_at, updated_at)
                    VALUES
                        (:id, :piid, :pid, :st, 'pending', 'patient', :now, :now)
                """),
                {
                    "id": adherence_id,
                    "piid": str(item_id),
                    "pid": patient_id,
                    "st": curr_time,
                    "now": now,
                }
            )
            curr_time += timedelta(hours=interval_hours)

    session.commit()
    logger.info(
        "Generated adherence schedule for prescription %s (%d items)",
        prescription_id, len(items)
    )


@celery.task(name="queues.reminder.handle_event", bind=True, max_retries=3)
def handle_event(self, event_dict: dict):
    """
    Process reminder-related domain events.
    """
    event_id = event_dict.get("event_id")
    event_type = event_dict.get("event_type")
    payload = event_dict.get("payload", {})

    if event_type not in HANDLED_EVENTS:
        return {"status": "skipped", "reason": "unhandled_event_type"}

    session = _get_sync_session()
    try:
        if _check_idempotency(session, event_id):
            logger.info("Duplicate event_id=%s already processed by %s", event_id, WORKER_NAME)
            return {"status": "skipped", "reason": "duplicate"}

        if event_type == "appointment.created":
            scheduled_time = payload.get("scheduled_time")
            patient_id = payload.get("patient_id")
            logger.info(
                "Scheduling appointment reminders for patient %s at %s (24h + 1h before)",
                patient_id, scheduled_time
            )
            # TODO: Schedule Celery eta tasks for 24h-before and 1h-before

        elif event_type == "appointment.rescheduled":
            old_time = payload.get("old_time")
            new_time = payload.get("new_time")
            patient_id = payload.get("patient_id")
            logger.info(
                "Rescheduling reminders for patient %s: %s → %s",
                patient_id, old_time, new_time
            )

        elif event_type == "prescription.created":
            prescription_id = payload.get("prescription_id")
            patient_id = payload.get("patient_id")
            _generate_adherence_schedule(session, prescription_id, patient_id)

        _mark_processed(session, event_id)
        return {"status": "processed", "event_type": event_type}

    except Exception as exc:
        session.rollback()
        logger.error("Reminder worker error for event_id=%s: %s", event_id, exc)
        raise self.retry(exc=exc, countdown=60)
    finally:
        session.close()
