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
from app.modules.consultation.service import ConsultationService
from app.modules.consultation.schemas import ConsultationUpdate, ConsultationDiagnosisCreate
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
    appt_id = uuid.uuid4()
    
    async with uow:
        # Create test organization
        org = Organization(id=org_id, name="Consultations Test Hospital", status="active")
        uow.session.add(org)
        
        # Create clinic
        clinic = Clinic(
            id=clinic_id,
            organization_id=org_id,
            name="Consultations Testing Center",
            timezone="UTC",
            status="active"
        )
        uow.session.add(clinic)
        
        # Create Doctor Profile & Entity
        doc_email = f"doc.consultation.{uuid.uuid4().hex[:6]}@test.com"
        doc_profile = Profile(id=doc_id, email=doc_email, first_name="Doc", last_name="Encounter")
        uow.session.add(doc_profile)
        await uow.flush()
        
        doctor = Doctor(
            id=doc_id,
            organization_id=org_id,
            specialty="Cardiology",
            license_number=f"LIC-CON-{uuid.uuid4().hex[:6]}",
            timezone="UTC",
            accepting_patients=True
        )
        uow.session.add(doctor)
        
        # Create Patient Profile & Entity
        pat_email = f"patient.consultation.{uuid.uuid4().hex[:6]}@test.com"
        pat_profile = Profile(id=pat_id, email=pat_email, first_name="Pat", last_name="Encounter")
        uow.session.add(pat_profile)
        await uow.flush()
        
        patient = Patient(
            id=pat_id,
            organization_id=org_id,
            mrn=f"MRN-CON-{uuid.uuid4().hex[:6]}",
            primary_doctor_id=doc_id,
            status="active"
        )
        uow.session.add(patient)
        await uow.flush()
        
        # Create an Appointment to initiate consultation from
        appointment = Appointment(
            id=appt_id,
            patient_id=pat_id,
            doctor_id=doc_id,
            clinic_id=clinic_id,
            scheduled_time=datetime.now(timezone.utc),
            duration=30,
            status="scheduled",
            booked_by=pat_id
        )
        uow.session.add(appointment)
        
    return {"clinic_id": clinic_id, "doctor_id": doc_id, "patient_id": pat_id, "appointment_id": appt_id}

@pytest.mark.anyio
async def test_consultation_clinical_workflow(test_session, test_data):
    uow = APIUnitOfWork(test_session)
    service = ConsultationService(uow)
    
    appt_id = test_data["appointment_id"]
    doc_id = test_data["doctor_id"]
    
    # 1. Start Consultation (Initializes session, returns LiveKit details)
    async with uow:
        session_info = await service.start_consultation(
            appointment_id=appt_id,
            actor_id=doc_id,
            actor_name="Dr. Jane Doe"
        )
        assert session_info["appointment_id"] == appt_id
        assert session_info["token"] is not None
        assert "room-" in session_info["room_id"]
        
        # Verify appointment transitioned to in_consultation
        appt = await uow.appointments.get(appt_id)
        assert appt.status == "in_consultation"

    # 2. Update SOAP Notes (clinician documenting findings)
    soap_input = {
        "subjective": "Patient reports mild chest tightness after exercise.",
        "objective": "BP 120/80, HR 72 bpm. Lungs clear.",
        "assessment": "Angina suspected, further testing needed.",
        "plan": "Schedule ECG next week."
    }
    update_in = ConsultationUpdate(
        chief_complaint="Mild chest tightness",
        soap_notes=soap_input
    )
    async with uow:
        consult = await service.update_consultation(
            appointment_id=appt_id,
            obj_in=update_in,
            actor_id=doc_id
        )
        assert consult.chief_complaint == "Mild chest tightness"
        assert consult.soap_notes["subjective"] == soap_input["subjective"]

    # 3. Add Diagnoses to encounter
    diagnosis_in = ConsultationDiagnosisCreate(
        condition_code="ICD-I20.9",
        name="Angina pectoris, unspecified",
        category="primary"
    )
    async with uow:
        diag = await service.add_diagnosis(
            appointment_id=appt_id,
            obj_in=diagnosis_in,
            actor_id=doc_id
        )
        assert diag.condition_code == "ICD-I20.9"
        assert diag.name == "Angina pectoris, unspecified"

    # 4. Complete Consultation (Freezes status and completed appointment)
    async with uow:
        completed_consult = await service.complete_consultation(
            appointment_id=appt_id,
            actor_id=doc_id
        )
        assert completed_consult.status == "completed"
        assert completed_consult.ended_at is not None
        
        # Verify parent appointment is completed
        appt = await uow.appointments.get(appt_id)
        assert appt.status == "completed"

    # 5. Enforce Immutability (Updates should now fail on completed consultations)
    async with uow:
        with pytest.raises(HTTPException) as exc_info:
            await service.update_consultation(
                appointment_id=appt_id,
                obj_in=update_in,
                actor_id=doc_id
            )
        assert exc_info.value.status_code == 400
        assert "Cannot modify a completed consultation" in exc_info.value.detail
