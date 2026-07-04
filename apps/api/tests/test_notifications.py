"""
Notification Delivery & Twilio Integration Tests.

Verifies:
  1. Profile lookup and channel selection (SMS if phone exists, fallback to Email).
  2. MockTwilioProvider SMS delivery simulation and logging to in-memory ledger.
  3. Correct Insertion of Notification and NotificationDelivery rows in the database.
  4. Idempotency guard for event handling.
"""
import pytest
import uuid
import sys
import os
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Add path mapping
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "worker")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages", "backend-core")))

from database.models import Profile, Notification, NotificationDelivery, ProcessedEvent
from queues.notification import handle_event, twilio_provider, fcm_provider

# Test DB connection
TEST_DB_URL = "postgresql+asyncpg://postgres:password@localhost:5433/healthcare"

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="module")
async def test_session(anyio_backend):
    engine = create_async_engine(TEST_DB_URL, future=True)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session
    await engine.dispose()

@pytest.fixture(scope="module")
async def test_profiles(test_session):
    profile_sms_id = uuid.uuid4()
    profile_email_id = uuid.uuid4()

    async with AsyncSession(test_session.bind) as session:
        p_sms = Profile(
            id=profile_sms_id,
            email=f"sms.user.{uuid.uuid4().hex[:6]}@test.com",
            first_name="SMS",
            last_name="User",
            phone="+15550199283"
        )
        p_email = Profile(
            id=profile_email_id,
            email=f"email.user.{uuid.uuid4().hex[:6]}@test.com",
            first_name="Email",
            last_name="User",
            phone=None
        )
        session.add(p_sms)
        session.add(p_email)
        await session.commit()

    return {"sms_profile_id": profile_sms_id, "email_profile_id": profile_email_id}


@pytest.mark.anyio
async def test_sms_and_push_delivery_flow(test_session, test_profiles):
    """
    Verifies that when a profile has a phone number, delivery routes to SMS primary,
    and dispatches a Push notification to FCM.
    """
    twilio_provider.clear_log()
    fcm_provider.clear_log()

    event_id = str(uuid.uuid4())
    event_dict = {
        "event_id": event_id,
        "event_type": "appointment.created",
        "payload": {
            "patient_id": str(test_profiles["sms_profile_id"]),
            "scheduled_time": "2026-07-05T10:00:00"
        }
    }

    res = handle_event(event_dict)
    assert res["status"] == "processed"

    # Assert Twilio SMS
    sms_logs = twilio_provider.get_message_log()
    assert len(sms_logs) == 1
    assert sms_logs[0]["to"] == "+15550199283"

    # Assert FCM Push
    fcm_logs = fcm_provider.get_message_log()
    assert len(fcm_logs) == 1
    assert fcm_logs[0]["token"] == f"fcm_mock_token_{test_profiles['sms_profile_id'].hex[:12]}"

    # Query DB to verify Notification and multiple NotificationDelivery channels exist
    async with AsyncSession(test_session.bind) as session:
        q_notif = select(Notification).filter(Notification.recipient_id == test_profiles["sms_profile_id"])
        res_notif = await session.execute(q_notif)
        notif = res_notif.scalars().first()
        assert notif is not None

        # Verify both SMS and Push deliveries were recorded
        q_deliv = select(NotificationDelivery).filter(NotificationDelivery.notification_id == notif.id)
        res_deliv = await session.execute(q_deliv)
        deliveries = res_deliv.scalars().all()
        assert len(deliveries) == 2

        channels = [d.channel for d in deliveries]
        assert "sms" in channels
        assert "push" in channels
        assert all(d.status == "sent" for d in deliveries)


@pytest.mark.anyio
async def test_email_and_push_delivery_flow(test_session, test_profiles):
    """
    Verifies that when a profile has no phone number, delivery routes to Email primary,
    and dispatches a Push notification to FCM.
    """
    twilio_provider.clear_log()
    fcm_provider.clear_log()

    event_id = str(uuid.uuid4())
    event_dict = {
        "event_id": event_id,
        "event_type": "prescription.created",
        "payload": {
            "patient_id": str(test_profiles["email_profile_id"]),
            "item_count": 3
        }
    }

    res = handle_event(event_dict)
    assert res["status"] == "processed"

    # Assert FCM Push
    fcm_logs = fcm_provider.get_message_log()
    assert len(fcm_logs) == 1
    assert fcm_logs[0]["token"] == f"fcm_mock_token_{test_profiles['email_profile_id'].hex[:12]}"

    async with AsyncSession(test_session.bind) as session:
        q_notif = select(Notification).filter(Notification.recipient_id == test_profiles["email_profile_id"])
        res_notif = await session.execute(q_notif)
        notif = res_notif.scalars().first()
        assert notif is not None

        # Verify both Email and Push deliveries were recorded
        q_deliv = select(NotificationDelivery).filter(NotificationDelivery.notification_id == notif.id)
        res_deliv = await session.execute(q_deliv)
        deliveries = res_deliv.scalars().all()
        assert len(deliveries) == 2

        channels = [d.channel for d in deliveries]
        assert "email" in channels
        assert "push" in channels
        assert all(d.status == "sent" for d in deliveries)


@pytest.mark.anyio
async def test_notification_idempotency(test_session, test_profiles):
    """
    Verifies duplicate events are skipped.
    """
    event_id = str(uuid.uuid4())
    event_dict = {
        "event_id": event_id,
        "event_type": "consultation.completed",
        "payload": {
            "patient_id": str(test_profiles["sms_profile_id"])
        }
    }

    res1 = handle_event(event_dict)
    assert res1["status"] == "processed"

    res2 = handle_event(event_dict)
    assert res2["status"] == "skipped"
    assert res2["reason"] == "duplicate"

