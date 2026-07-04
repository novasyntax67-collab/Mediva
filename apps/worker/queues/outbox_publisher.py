"""
Outbox Publisher — Celery Beat task that polls the event_outbox table and
dispatches pending events to the EventBus (Celery workers via Redis).

Key design decisions:
  - Uses SELECT ... FOR UPDATE SKIP LOCKED for safe concurrent polling.
  - Batch updates — publishes and marks a batch at once to reduce write amplification.
  - Exponential backoff — failed events are retried at increasing intervals.
  - Dead-letter — events exceeding max_retries are marked 'failed' permanently.
  - Distinguishes transient vs permanent failures:
      * Transient (Redis down, timeout) → retry with backoff.
      * Permanent (invalid payload, schema mismatch) → dead-letter immediately.
"""
import os
import sys
import logging
from datetime import datetime, timezone, timedelta

# Add backend-core to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages", "backend-core")))

from celery_app import celery
from events.base import DomainEvent
from events.bus import CeleryEventBus

logger = logging.getLogger(__name__)

# Configurable via environment
OUTBOX_BATCH_SIZE = int(os.getenv("OUTBOX_BATCH_SIZE", "50"))

# Exponential backoff delays (in minutes) indexed by retry_count
BACKOFF_SCHEDULE = [1, 5, 15, 60, 240]  # 1m → 5m → 15m → 1h → 4h → dead-letter

event_bus = CeleryEventBus(celery)


def _get_sync_session():
    """Create a synchronous database session for the worker process."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5433/healthcare"
    )
    # Convert async URL to sync if needed
    sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    return Session()


@celery.task(name="queues.outbox_publisher.publish_pending_events")
def publish_pending_events():
    """
    Polls event_outbox for pending rows, dispatches them to the EventBus,
    and marks them as published or failed.

    Runs on Celery Beat at a configurable interval (default: every 5 seconds).
    """
    from database.models import EventOutbox

    session = _get_sync_session()
    now = datetime.now(timezone.utc)

    try:
        # 1. Fetch pending events that are ready for publishing
        #    Skip rows that are being processed by another worker instance (SKIP LOCKED)
        #    Skip rows whose next_retry_at is in the future (backoff)
        from sqlalchemy import text

        rows = session.execute(
            text("""
                SELECT id, event_type, payload, retry_count, max_retries
                FROM event_outbox
                WHERE status = 'pending'
                  AND (next_retry_at IS NULL OR next_retry_at <= :now)
                ORDER BY created_at ASC
                LIMIT :batch_size
                FOR UPDATE SKIP LOCKED
            """),
            {"now": now, "batch_size": OUTBOX_BATCH_SIZE}
        ).fetchall()

        if not rows:
            return {"published": 0, "failed": 0}

        published_ids = []
        failed_updates = []

        # 2. Attempt to publish each event
        for row in rows:
            row_id, event_type, payload_dict, retry_count, max_retries = row

            try:
                event = DomainEvent.from_dict(payload_dict)
                event_bus.publish(event)
                published_ids.append(str(row_id))

            except (KeyError, TypeError, ValueError) as exc:
                # Permanent failure — invalid payload, schema mismatch
                # Dead-letter immediately, don't waste retries
                logger.error(
                    "Permanent failure for outbox event %s: %s", row_id, exc
                )
                failed_updates.append({
                    "id": str(row_id),
                    "status": "failed",
                    "last_error": f"PERMANENT: {type(exc).__name__}: {exc}",
                    "retry_count": retry_count,
                })

            except Exception as exc:
                # Transient failure — Redis down, network timeout, etc.
                new_retry = retry_count + 1
                if new_retry >= max_retries:
                    # Exceeded max retries → dead-letter
                    logger.error(
                        "Dead-lettered outbox event %s after %d retries: %s",
                        row_id, new_retry, exc
                    )
                    failed_updates.append({
                        "id": str(row_id),
                        "status": "failed",
                        "last_error": f"TRANSIENT (max retries): {type(exc).__name__}: {exc}",
                        "retry_count": new_retry,
                    })
                else:
                    # Schedule retry with exponential backoff
                    backoff_idx = min(new_retry - 1, len(BACKOFF_SCHEDULE) - 1)
                    delay_minutes = BACKOFF_SCHEDULE[backoff_idx]
                    next_retry = now + timedelta(minutes=delay_minutes)

                    logger.warning(
                        "Transient failure for outbox event %s (retry %d/%d, next at %s): %s",
                        row_id, new_retry, max_retries, next_retry, exc
                    )
                    failed_updates.append({
                        "id": str(row_id),
                        "status": "pending",  # Keep pending for retry
                        "last_error": f"TRANSIENT: {type(exc).__name__}: {exc}",
                        "retry_count": new_retry,
                        "next_retry_at": next_retry,
                    })

        # 3. Batch update published rows
        if published_ids:
            session.execute(
                text("""
                    UPDATE event_outbox
                    SET status = 'published', published_at = :now
                    WHERE id = ANY(:ids ::uuid[])
                """),
                {"now": now, "ids": published_ids}
            )

        # 4. Batch update failed/retried rows
        for update in failed_updates:
            params = {
                "id": update["id"],
                "status": update["status"],
                "last_error": update["last_error"],
                "retry_count": update["retry_count"],
            }
            next_retry_clause = ""
            if "next_retry_at" in update:
                params["next_retry_at"] = update["next_retry_at"]
                next_retry_clause = ", next_retry_at = :next_retry_at"

            session.execute(
                text(f"""
                    UPDATE event_outbox
                    SET status = :status, last_error = :last_error,
                        retry_count = :retry_count{next_retry_clause}
                    WHERE id = :id ::uuid
                """),
                params
            )

        session.commit()

        result = {"published": len(published_ids), "failed": len(failed_updates)}
        if published_ids:
            logger.info("Outbox publisher: %s", result)
        return result

    except Exception as exc:
        session.rollback()
        logger.error("Outbox publisher critical error: %s", exc)
        raise
    finally:
        session.close()
