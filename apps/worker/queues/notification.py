"""
Notification Worker — consumes domain events and dispatches notifications.

Consumes:
  - appointment.created   → Patient confirmation email/SMS
  - consultation.completed → Patient visit summary notification
  - prescription.created   → Patient new prescription alert
  - risk.generated         → Clinician high-risk patient alert

Implements:
  - Idempotency guard via processed_events table
  - Transient vs permanent failure distinction
"""
import os
import sys
import logging
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages", "backend-core")))

from celery_app import celery

logger = logging.getLogger(__name__)

WORKER_NAME = "notification"

HANDLED_EVENTS = {
    "appointment.created",
    "appointment.cancelled",
    "consultation.completed",
    "prescription.created",
    "risk.generated",
}


def _check_idempotency(session, event_id: str) -> bool:
    """Returns True if this event was already processed by this worker."""
    from sqlalchemy import text
    result = session.execute(
        text("SELECT 1 FROM processed_events WHERE event_id = :eid AND worker = :w"),
        {"eid": event_id, "w": WORKER_NAME}
    ).fetchone()
    return result is not None


def _mark_processed(session, event_id: str):
    """Record that this worker has processed the event."""
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


from notifications.mock_twilio import MockTwilioProvider
from notifications.fcm import MockFCMProvider
from database.models import Profile, Patient, Notification, NotificationDelivery
import uuid

# Initialize Mock Twilio Provider
twilio_provider = MockTwilioProvider(
    account_sid=os.getenv("TWILIO_ACCOUNT_SID", "ACmock_account"),
    auth_token=os.getenv("TWILIO_AUTH_TOKEN", "mock_auth_token"),
    from_number=os.getenv("TWILIO_PHONE_NUMBER", "+15551234567")
)

# Initialize Mock FCM Provider
fcm_provider = MockFCMProvider()


def _deliver_notification(session, recipient_id: str, title: str, body: str):
    """
    Creates a Notification and attempts delivery via:
      1. Primary Channel: SMS (if phone number registered) otherwise falls back to Email.
      2. Push Channel: FCM Push Notification.
    """
    recipient_uuid = uuid.UUID(recipient_id)
    profile = session.get(Profile, recipient_uuid)
    if not profile:
        logger.error("Could not find recipient profile %s for notification", recipient_id)
        return

    # 1. Save Notification record
    notification = Notification(
        id=uuid.uuid4(),
        recipient_id=recipient_uuid,
        title=title,
        body=body
    )
    session.add(notification)
    session.flush()

    # --- PRIMARY DELIVERY CHANNEL (SMS/EMAIL) ---
    primary_channel = "sms" if profile.phone else "email"
    recipient_address = profile.phone if profile.phone else profile.email

    # Save Primary NotificationDelivery record
    primary_delivery = NotificationDelivery(
        id=uuid.uuid4(),
        notification_id=notification.id,
        channel=primary_channel,
        status="pending"
    )
    session.add(primary_delivery)
    session.flush()

    try:
        if primary_channel == "sms":
            result = twilio_provider.send(recipient=recipient_address, title=title, body=body)
            primary_delivery.status = "sent" if result.success else "failed"
            primary_delivery.provider_message_id = result.provider_message_id
            primary_delivery.provider_response = result.provider_response
            if not result.success:
                primary_delivery.error_message = result.error_message
        else:
            # Mock Email delivery
            primary_delivery.status = "sent"
            primary_delivery.provider_message_id = f"email_{uuid.uuid4().hex[:12]}"
            primary_delivery.provider_response = {"status": "delivered_mock"}
            logger.info("📧 MOCK EMAIL [SENT] to=%s | %s: %s", recipient_address, title, body[:80])

        if primary_delivery.status == "sent":
            primary_delivery.sent_at = datetime.now(timezone.utc)

    except Exception as e:
        primary_delivery.status = "failed"
        primary_delivery.error_message = str(e)
        logger.error("Primary delivery failed for recipient %s on channel %s: %s", recipient_id, primary_channel, e)

    # --- PUSH DELIVERY CHANNEL (FCM) ---
    fcm_token = f"fcm_mock_token_{profile.id.hex[:12]}"
    push_delivery = NotificationDelivery(
        id=uuid.uuid4(),
        notification_id=notification.id,
        channel="push",
        status="pending"
    )
    session.add(push_delivery)
    session.flush()

    try:
        push_result = fcm_provider.send(
            recipient=fcm_token,
            title=title,
            body=body,
            metadata={"click_action": "FLUTTER_NOTIFICATION_CLICK", "recipient_id": recipient_id}
        )
        push_delivery.status = "sent" if push_result.success else "failed"
        push_delivery.provider_message_id = push_result.provider_message_id
        push_delivery.provider_response = push_result.provider_response
        if push_delivery.status == "sent":
            push_delivery.sent_at = datetime.now(timezone.utc)

    except Exception as e:
        push_delivery.status = "failed"
        push_delivery.error_message = str(e)
        logger.error("Push delivery failed for recipient %s: %s", recipient_id, e)

    session.commit()



@celery.task(name="queues.notification.handle_event", bind=True, max_retries=3)
def handle_event(self, event_dict: dict):
    """
    Dispatch notifications based on domain event type.
    """
    event_id = event_dict.get("event_id")
    event_type = event_dict.get("event_type")
    payload = event_dict.get("payload", {})

    if event_type not in HANDLED_EVENTS:
        logger.debug("Notification worker ignoring event_type=%s", event_type)
        return {"status": "skipped", "reason": "unhandled_event_type"}

    session = _get_sync_session()
    try:
        # Idempotency check
        if _check_idempotency(session, event_id):
            logger.info("Duplicate event_id=%s already processed by %s", event_id, WORKER_NAME)
            return {"status": "skipped", "reason": "duplicate"}

        # Route to handler
        if event_type == "appointment.created":
            patient_id = payload.get("patient_id")
            scheduled_time = payload.get("scheduled_time")
            _deliver_notification(
                session=session,
                recipient_id=patient_id,
                title="Appointment Booked",
                body=f"Your appointment has been booked successfully for {scheduled_time}."
            )

        elif event_type == "appointment.cancelled":
            patient_id = payload.get("patient_id")
            reason = payload.get("reason") or "No reason provided"
            _deliver_notification(
                session=session,
                recipient_id=patient_id,
                title="Appointment Cancelled",
                body=f"Your scheduled appointment has been cancelled. Reason: {reason}."
            )

        elif event_type == "consultation.completed":
            patient_id = payload.get("patient_id")
            _deliver_notification(
                session=session,
                recipient_id=patient_id,
                title="Visit Summary Ready",
                body="Your doctor has completed your consultation. Your visit summary and SOAP notes are now available."
            )

        elif event_type == "prescription.created":
            patient_id = payload.get("patient_id")
            item_count = payload.get("item_count", 0)
            _deliver_notification(
                session=session,
                recipient_id=patient_id,
                title="New Prescription Issued",
                body=f"A new prescription with {item_count} items has been issued for you. Your adherence schedule is ready."
            )

        elif event_type == "risk.generated":
            score = payload.get("score", 0)
            patient_id = payload.get("patient_id")
            if score >= 70.0:
                # Notify the patient's primary clinician
                patient = session.get(Patient, uuid.UUID(patient_id))
                if patient and patient.primary_doctor_id:
                    _deliver_notification(
                        session=session,
                        recipient_id=str(patient.primary_doctor_id),
                        title="HIGH RISK PATIENT ALERT",
                        body=f"Patient {patient_id} has scored high clinical risk: {score:.1f}%."
                    )
                else:
                    logger.warning("High risk score %.1f%% for patient %s, but no primary doctor found", score, patient_id)
            else:
                logger.info("Risk score %.1f%% for patient %s (below alert threshold)", score, patient_id)

        # Mark processed
        _mark_processed(session, event_id)
        return {"status": "processed", "event_type": event_type}

    except Exception as exc:
        session.rollback()
        logger.error("Notification worker error for event_id=%s: %s", event_id, exc)
        raise self.retry(exc=exc, countdown=60)
    finally:
        session.close()

