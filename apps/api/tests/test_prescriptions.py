import pytest
import asyncio
import uuid
import sys
import os
from datetime import date, datetime, time, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi import HTTPException
from sqlalchemy.future import select

# Add path mapping
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages", "backend-core")))

from app.core.unit_of_work import APIUnitOfWork
from app.modules.prescriptions.service import PrescriptionService
from app.modules.prescriptions.schemas import PrescriptionCreate, PrescriptionItemCreate, MedicationAdherenceLog
from database.models import (
    Profile, Organization, Clinic, Doctor, Patient, Appointment,
    Consultation, MedicationAdherence, EventOutbox
)

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
    appt_id = uuid.uuid4()
    
    async with uow:
        # Create test organization
        org = Organization(id=org_id, name="Prescription Test Hospital", status="active")
        uow.session.add(org)
        
        # Create clinic
        clinic = Clinic(
            id=clinic_id,
            organization_id=org_id,
            name="Prescription Testing Center",
            timezone="UTC",
            status="active"
        )
        uow.session.add(clinic)
        
        # Create Doctor Profile & Entity
        doc_email = f"doc.prescription.{uuid.uuid4().hex[:6]}@test.com"
        doc_profile = Profile(id=doc_id, email=doc_email, first_name="Doc", last_name="Prescription")
        uow.session.add(doc_profile)
        await uow.flush()
        
        doctor = Doctor(
            id=doc_id,
            organization_id=org_id,
            specialty="Pediatrics",
            license_number=f"LIC-PRE-{uuid.uuid4().hex[:6]}",
            timezone="UTC",
            accepting_patients=True
        )
        uow.session.add(doctor)
        
        # Create Patient Profile & Entity
        pat_email = f"patient.prescription.{uuid.uuid4().hex[:6]}@test.com"
        pat_profile = Profile(id=pat_id, email=pat_email, first_name="Pat", last_name="Prescription")
        uow.session.add(pat_profile)
        await uow.flush()
        
        patient = Patient(
            id=pat_id,
            organization_id=org_id,
            mrn=f"MRN-PRE-{uuid.uuid4().hex[:6]}",
            primary_doctor_id=doc_id,
            status="active"
        )
        uow.session.add(patient)
        await uow.flush()
        
        # Create Appointment & Consultation
        appointment = Appointment(
            id=appt_id,
            patient_id=pat_id,
            doctor_id=doc_id,
            clinic_id=clinic_id,
            scheduled_time=datetime.now(timezone.utc),
            duration=30,
            status="in_consultation",
            booked_by=pat_id
        )
        uow.session.add(appointment)
        await uow.flush()
        
        consultation = Consultation(
            appointment_id=appt_id,
            room_id=f"room-{appt_id}",
            status="in_progress",
            started_at=datetime.now(timezone.utc)
        )
        uow.session.add(consultation)
        
    return {"clinic_id": clinic_id, "doctor_id": doc_id, "patient_id": pat_id, "appointment_id": appt_id}

@pytest.mark.anyio
async def test_prescription_clinical_workflow(test_session, test_data):
    uow = APIUnitOfWork(test_session)
    service = PrescriptionService(uow)
    
    appt_id = test_data["appointment_id"]
    doc_id = test_data["doctor_id"]
    pat_id = test_data["patient_id"]
    
    # 1. Create Prescription
    item_a = PrescriptionItemCreate(
        medication_name=f"Amoxicillin-{uuid.uuid4().hex[:4]}",
        dosage_quantity=500.0,
        dosage_unit="mg",
        frequency_interval=12,
        frequency_period="hour",
        duration_days=3,
        quantity=6,
        refills=0,
        instructions="Take with food"
    )
    
    prescription_in = PrescriptionCreate(
        consultation_id=appt_id,
        items=[item_a]
    )
    
    async with uow:
        prescription = await service.create_prescription(
            consultation_id=appt_id,
            obj_in=prescription_in,
            actor_id=doc_id
        )
        assert prescription.id is not None
        assert len(prescription.items) == 1

    # 2. Verify prescription.created event was written to the outbox atomically
    query_outbox = select(EventOutbox).filter(
        EventOutbox.event_type == "prescription.created",
        EventOutbox.aggregate_id == prescription.id,
        EventOutbox.status == "pending"
    )
    res_outbox = await test_session.execute(query_outbox)
    outbox_row = res_outbox.scalars().first()
    assert outbox_row is not None
    assert outbox_row.payload["payload"]["prescription_id"] == str(prescription.id)
    assert outbox_row.payload["payload"]["item_count"] == 1

    # 3. Test adherence logging (create a schedule entry manually for unit test)
    p_item_id = prescription.items[0].id
    adh_id = uuid.uuid4()
    async with uow:
        adherence = MedicationAdherence(
            id=adh_id,
            prescription_item_id=p_item_id,
            patient_id=pat_id,
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=12),
            status="pending",
            source="patient"
        )
        uow.session.add(adherence)

    # 4. Patient logs compliance
    log_in = MedicationAdherenceLog(status="taken", source="patient")
    async with uow:
        logged_record = await service.log_adherence(
            adherence_id=adh_id,
            log_in=log_in,
            actor_id=pat_id
        )
        assert logged_record.status == "taken"
        assert logged_record.logged_time is not None
        assert logged_record.logged_by == pat_id

    # 5. Prevent double-logging same schedule slot
    async with uow:
        with pytest.raises(HTTPException) as exc_info:
            await service.log_adherence(
                adherence_id=adh_id,
                log_in=log_in,
                actor_id=pat_id
            )
        assert exc_info.value.status_code == 400
        assert "already logged" in exc_info.value.detail

