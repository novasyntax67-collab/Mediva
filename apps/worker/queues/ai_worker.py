"""
AI Worker — LLM-oriented asynchronous processing.

Handles workloads that may take variable time (2s to 30s+) and should
never block the API. Separated from the Risk Worker because LLM calls
have different scaling, cost, and reliability characteristics.

Consumes:
  - consultation.completed → Generate clinical summaries, embed notes
  - vital.recorded         → (future) anomaly pattern detection via ML

Responsibilities:
  - Summaries (LLM-generated SOAP summaries)
  - OCR (document scanning)
  - Embeddings (vector index for RAG retrieval)
  - RAG (retrieval-augmented clinical guidance)

Implements:
  - Idempotency guard via processed_events table
"""
import os
import sys
import logging
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages", "backend-core")))

from celery_app import celery

logger = logging.getLogger(__name__)

WORKER_NAME = "ai"

HANDLED_EVENTS = {
    "consultation.completed",
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


@celery.task(name="queues.ai_worker.handle_event", bind=True, max_retries=2)
def handle_event(self, event_dict: dict):
    """
    Process AI-oriented tasks from domain events.
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

        if event_type == "consultation.completed":
            appointment_id = payload.get("appointment_id")
            patient_id = payload.get("patient_id")
            logger.info(
                "AI Worker: Generating clinical summary for consultation %s (patient %s)",
                appointment_id, patient_id
            )
            # TODO: Call LLM to generate SOAP summary, embed into vector store

        _mark_processed(session, event_id)
        return {"status": "processed", "event_type": event_type}

    except Exception as exc:
        session.rollback()
        logger.error("AI worker error for event_id=%s: %s", event_id, exc)
        raise self.retry(exc=exc, countdown=120)  # Longer retry for LLM tasks
    finally:
        session.close()
