import pytest
import asyncio
import uuid
import sys
import os
from datetime import date, datetime, time, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi import HTTPException

# Add path mapping
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "packages", "backend-core")))

from app.core.unit_of_work import APIUnitOfWork
from app.modules.appointments.booking_service import AppointmentBookingService
from database.models import Profile, Organization, Clinic, Doctor, Patient, Appointment

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
    clinic_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    pat_id = uuid.uuid4()
    
    async with uow:
        # Create test organization
        org = Organization(id=org_id, name="Availability Test Hospital", status="active")
        uow.session.add(org)
        
        # Create clinic
        clinic = Clinic(
            id=clinic_id,
            organization_id=org_id,
            name="Appointments Testing Center",
            timezone="UTC",
            status="active"
        )
        uow.session.add(clinic)
        
        # Create Doctor Profile & Entity
        doc_email = f"doc.availability.{uuid.uuid4().hex[:6]}@test.com"
        doc_profile = Profile(id=doc_id, email=doc_email, first_name="Doc", last_name="Schedule")
        uow.session.add(doc_profile)
        await uow.flush()
        
        doctor = Doctor(
            id=doc_id,
            organization_id=org_id,
            specialty="Cardiology",
            license_number=f"LIC-SCH-{uuid.uuid4().hex[:6]}",
            timezone="UTC",
            accepting_patients=True,
            # Availability template: Monday (day 1) 9 AM to 1 PM
            availability_template={
                "weekly": {
                    "1": [{"start": "09:00", "end": "13:00"}]
                }
            }
        )
        uow.session.add(doctor)
        
        # Create Patient Profile & Entity
        pat_email = f"patient.availability.{uuid.uuid4().hex[:6]}@test.com"
        pat_profile = Profile(id=pat_id, email=pat_email, first_name="Pat", last_name="Schedule")
        uow.session.add(pat_profile)
        await uow.flush()
        
        patient = Patient(
            id=pat_id,
            organization_id=org_id,
            mrn=f"MRN-SCH-{uuid.uuid4().hex[:6]}",
            primary_doctor_id=doc_id,
            status="active"
        )
        uow.session.add(patient)
        
    return {"org_id": org_id, "clinic_id": clinic_id, "doctor_id": doc_id, "patient_id": pat_id}

@pytest.mark.anyio
async def test_appointment_scheduling_engine(test_session, test_data):
    uow = APIUnitOfWork(test_session)
    booking_service = AppointmentBookingService(uow)
    
    pat_id = test_data["patient_id"]
    doc_id = test_data["doctor_id"]
    clinic_id = test_data["clinic_id"]
    
    # Target date: A future Monday (e.g. 2026-07-06 is a Monday)
    target_monday = date(2026, 7, 6)
    
    # 1. Test Successful Booking (Inside template)
    slot_time = datetime.combine(target_monday, time(9, 0), tzinfo=timezone.utc)
    async with uow:
        appt = await booking_service.book_appointment(
            patient_id=pat_id,
            doctor_id=doc_id,
            clinic_id=clinic_id,
            scheduled_time=slot_time,
            duration_minutes=30,
            reason="Routine checkup",
            actor_id=pat_id
        )
        assert appt.id is not None
        assert appt.status == "scheduled"

    # 2. Test Booking Unavailable Slot (Outside template range e.g. 2 PM)
    outside_time = datetime.combine(target_monday, time(14, 0), tzinfo=timezone.utc)
    async with uow:
        with pytest.raises(HTTPException) as exc_info:
            await booking_service.book_appointment(
                patient_id=pat_id,
                doctor_id=doc_id,
                clinic_id=clinic_id,
                scheduled_time=outside_time,
                duration_minutes=30,
                reason="Should fail",
                actor_id=pat_id
            )
        assert exc_info.value.status_code == 409

    # 3. Test Booking Overlapping Slot (Already booked at 9 AM)
    async with uow:
        with pytest.raises(HTTPException) as exc_info:
            await booking_service.book_appointment(
                patient_id=pat_id,
                doctor_id=doc_id,
                clinic_id=clinic_id,
                scheduled_time=slot_time,
                duration_minutes=30,
                reason="Duplicate",
                actor_id=pat_id
            )
        assert exc_info.value.status_code == 409

@pytest.mark.anyio
async def test_booking_concurrency_race_condition(test_session, test_data):
    """
    Triggers concurrent booking attempts for the same slot.
    Row-level locking must guarantee that only one booking succeeds while the other fails.
    """
    pat_id = test_data["patient_id"]
    doc_id = test_data["doctor_id"]
    clinic_id = test_data["clinic_id"]
    target_monday = date(2026, 7, 6)
    
    # Try booking 10 AM slot in parallel
    slot_time = datetime.combine(target_monday, time(10, 0), tzinfo=timezone.utc)
    
    # We establish separate transactions
    async def attempt_booking():
        # Create unique session for parallel transaction
        engine = create_async_engine(TEST_DB_URL, future=True)
        session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with session_maker() as session:
            uow = APIUnitOfWork(session)
            booking_service = AppointmentBookingService(uow)
            async with uow:
                await booking_service.book_appointment(
                    patient_id=pat_id,
                    doctor_id=doc_id,
                    clinic_id=clinic_id,
                    scheduled_time=slot_time,
                    duration_minutes=30,
                    reason="Concurrent attempt",
                    actor_id=pat_id
                )
        await engine.dispose()

    # Fire two concurrent booking tasks
    results = await asyncio.gather(
        attempt_booking(),
        attempt_booking(),
        return_exceptions=True
    )
    
    # Exactly one task should raise a 409 Conflict, while the other succeeds (returns None)
    successes = [r for r in results if r is None]
    failures = [r for r in results if isinstance(r, HTTPException) and r.status_code == 409]
    
    assert len(successes) == 1
    assert len(failures) == 1
