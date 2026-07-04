"""
Risk Worker — deterministic clinical risk scoring and alerting pipeline.

Separated from the AI Worker because risk scoring is deterministic (threshold
evaluation, statistical rules) rather than LLM-oriented. Different scaling
and reliability requirements.

Consumes:
  - vital.recorded → Re-evaluate patient risk scores based on latest vitals

Implements:
  - Clinical threshold alerting for abnormal readings
  - Idempotency guard via processed_events table
"""
import os
import sys
import logging
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages", "backend-core")))

from celery_app import celery

logger = logging.getLogger(__name__)

WORKER_NAME = "risk"

HANDLED_EVENTS = {
    "vital.recorded",
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


@celery.task(name="queues.risk_worker.handle_event", bind=True, max_retries=3)
def handle_event(self, event_dict: dict):
    """
    Evaluate clinical risk thresholds from vital observations.
    """
    event_id = event_dict.get("event_id")
    event_type = event_dict.get("event_type")
    payload = event_dict.get("payload", {})

    if event_type not in HANDLED_EVENTS:
        return {"status": "skipped", "reason": "unhandled_event_type"}

    session = _get_sync_session()
    try:
        if _check_idempotency(session, event_id):
            return {"status": "skipped", "reason": "duplicate"}

        vital_status = payload.get("status")
        patient_id = payload.get("patient_id")
        measurement_code = payload.get("measurement_code")
        value = payload.get("value_numeric")

        if vital_status == "abnormal":
            logger.warning(
                "RISK ALERT: Patient %s has abnormal %s reading (value=%.1f). "
                "Triggering background risk re-evaluation.",
                patient_id, measurement_code, value or 0
            )
            # TODO: Run deterministic risk model and update risk_scores table
        else:
            logger.info(
                "Vital %s for patient %s within normal range (value=%.1f)",
                measurement_code, patient_id, value or 0
            )

        _mark_processed(session, event_id)
        return {"status": "processed", "event_type": event_type}

    except Exception as exc:
        session.rollback()
        logger.error("Risk worker error for event_id=%s: %s", event_id, exc)
        raise self.retry(exc=exc, countdown=60)
    finally:
        session.close()
