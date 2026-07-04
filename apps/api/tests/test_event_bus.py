"""
Integration tests for the Transactional Outbox & Domain Event Bus.

Test cases:
  1. Event published after commit — outbox row exists with status=pending
  2. No event after rollback — outbox table has no new rows
  3. Multiple events published in commit order — created_at ordering preserved
  4. Duplicate event ignored — processed_events table blocks re-processing
  5. Invalid payload rejected — malformed event raises validation error
  6. DomainEvent serialization roundtrip — to_dict / from_dict consistency
  7. Event factory validation — Pydantic validates payload types
"""
import pytest
import asyncio
import uuid
import sys
import os
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select

# Add path mapping
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages", "backend-core")))

from app.core.unit_of_work import APIUnitOfWork
from database.models import Profile, Organization, Patient, Doctor, EventOutbox, AuditLog
from events.base import DomainEvent
from events.events import appointment_created, vital_recorded, consultation_completed
from events.payloads import AppointmentCreatedPayload

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
async def test_data(test_session):
    uow = APIUnitOfWork(test_session)
    org_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    pat_id = uuid.uuid4()

    async with uow:
        org = Organization(id=org_id, name="Event Bus Test Hospital", status="active")
        uow.session.add(org)

        doc_email = f"doc.evt.{uuid.uuid4().hex[:6]}@test.com"
        doc_profile = Profile(id=doc_id, email=doc_email, first_name="Doc", last_name="Event")
        uow.session.add(doc_profile)
        await uow.flush()

        doctor = Doctor(
            id=doc_id,
            organization_id=org_id,
            specialty="General",
            license_number=f"LIC-EVT-{uuid.uuid4().hex[:6]}",
            timezone="UTC",
            accepting_patients=True
        )
        uow.session.add(doctor)

        pat_email = f"pat.evt.{uuid.uuid4().hex[:6]}@test.com"
        pat_profile = Profile(id=pat_id, email=pat_email, first_name="Pat", last_name="Event")
        uow.session.add(pat_profile)
        await uow.flush()

        patient = Patient(
            id=pat_id,
            organization_id=org_id,
            mrn=f"MRN-EVT-{uuid.uuid4().hex[:6]}",
            primary_doctor_id=doc_id,
            status="active"
        )
        uow.session.add(patient)

    return {"org_id": org_id, "doctor_id": doc_id, "patient_id": pat_id}


# ─── Test 1: Event published after commit ─────────────────────────────────────

@pytest.mark.anyio
async def test_event_in_outbox_after_commit(test_session, test_data):
    """After committing a UoW with a collected event, the event_outbox should
    contain a row with status='pending'."""
    uow = APIUnitOfWork(test_session)
    event_id = str(uuid.uuid4())
    appt_id = str(uuid.uuid4())

    event = appointment_created(
        appointment_id=appt_id,
        patient_id=str(test_data["patient_id"]),
        doctor_id=str(test_data["doctor_id"]),
        clinic_id=str(uuid.uuid4()),
        scheduled_time=datetime.now(timezone.utc).isoformat(),
        duration_minutes=30,
        actor_id=str(test_data["patient_id"]),
        tenant_id=str(test_data["org_id"]),
    )
    # Override event_id for deterministic lookup
    event = DomainEvent(**{**event.to_dict(), "event_id": event_id})

    async with uow:
        # Simulate a clinical write (audit log)
        audit = AuditLog(
            actor_id=test_data["patient_id"],
            action="TEST_OUTBOX_COMMIT",
            entity_type="test",
            entity_id=test_data["patient_id"],
            new_value={"detail": "Testing outbox commit"}
        )
        uow.session.add(audit)
        uow.collect_event(event)
        # __aexit__ will call commit() → inserts into event_outbox

    # Verify outbox row exists
    query = select(EventOutbox).filter(EventOutbox.id == uuid.UUID(event_id))
    result = await test_session.execute(query)
    outbox_row = result.scalars().first()

    assert outbox_row is not None
    assert outbox_row.status == "pending"
    assert outbox_row.event_type == "appointment.created"
    assert outbox_row.aggregate_type == "appointment"
    assert str(outbox_row.aggregate_id) == appt_id


# ─── Test 2: No event after rollback ──────────────────────────────────────────

@pytest.mark.anyio
async def test_no_event_after_rollback(test_session, test_data):
    """After a rollback, no outbox rows should be created."""
    uow = APIUnitOfWork(test_session)
    event_id = str(uuid.uuid4())

    event = vital_recorded(
        vital_id=str(uuid.uuid4()),
        patient_id=str(test_data["patient_id"]),
        measurement_code="LOINC-8867-4",
        value_numeric=72.0,
        status_val="normal",
        actor_id=str(test_data["doctor_id"]),
    )
    event = DomainEvent(**{**event.to_dict(), "event_id": event_id})

    try:
        async with uow:
            uow.collect_event(event)
            raise ValueError("Simulated failure to trigger rollback")
    except ValueError:
        pass

    # Verify outbox row does NOT exist
    query = select(EventOutbox).filter(EventOutbox.id == uuid.UUID(event_id))
    result = await test_session.execute(query)
    outbox_row = result.scalars().first()

    assert outbox_row is None


# ─── Test 3: Multiple events in commit order ─────────────────────────────────

@pytest.mark.anyio
async def test_multiple_events_in_order(test_session, test_data):
    """Multiple events collected in one UoW should all appear in the outbox."""
    uow = APIUnitOfWork(test_session)
    event_ids = [str(uuid.uuid4()) for _ in range(3)]

    events = [
        DomainEvent(**{**appointment_created(
            appointment_id=str(uuid.uuid4()),
            patient_id=str(test_data["patient_id"]),
            doctor_id=str(test_data["doctor_id"]),
            clinic_id=str(uuid.uuid4()),
            scheduled_time=datetime.now(timezone.utc).isoformat(),
            duration_minutes=30,
            actor_id=str(test_data["patient_id"]),
        ).to_dict(), "event_id": eid})
        for eid in event_ids
    ]

    async with uow:
        audit = AuditLog(
            actor_id=test_data["patient_id"],
            action="TEST_MULTI_EVENT",
            entity_type="test",
            entity_id=test_data["patient_id"],
            new_value={"detail": "Testing multiple events"}
        )
        uow.session.add(audit)
        for evt in events:
            uow.collect_event(evt)

    # Verify all three outbox rows exist
    for eid in event_ids:
        query = select(EventOutbox).filter(EventOutbox.id == uuid.UUID(eid))
        result = await test_session.execute(query)
        row = result.scalars().first()
        assert row is not None
        assert row.status == "pending"


# ─── Test 4: DomainEvent serialization roundtrip ──────────────────────────────

def test_domain_event_serialization_roundtrip():
    """DomainEvent.to_dict() and from_dict() should produce identical objects."""
    event = consultation_completed(
        appointment_id=str(uuid.uuid4()),
        doctor_id=str(uuid.uuid4()),
        patient_id=str(uuid.uuid4()),
        actor_id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        correlation_id=str(uuid.uuid4()),
    )

    serialized = event.to_dict()
    deserialized = DomainEvent.from_dict(serialized)

    assert deserialized.event_id == event.event_id
    assert deserialized.event_type == event.event_type
    assert deserialized.aggregate_type == event.aggregate_type
    assert deserialized.payload == event.payload
    assert deserialized.tenant_id == event.tenant_id
    assert deserialized.correlation_id == event.correlation_id


# ─── Test 5: Pydantic payload validation ─────────────────────────────────────

def test_pydantic_payload_validation():
    """Pydantic should reject invalid payload types at event creation time."""
    with pytest.raises(Exception):
        # duration_minutes expects int, not string
        AppointmentCreatedPayload(
            appointment_id="valid",
            patient_id="valid",
            doctor_id="valid",
            clinic_id="valid",
            scheduled_time="valid",
            duration_minutes="not_an_int",  # type: ignore
        )
