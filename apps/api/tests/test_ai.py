import pytest
import asyncio
import uuid
import sys
import os
from datetime import date, datetime, time, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi import HTTPException
from sqlalchemy.future import select

# Add path mapping
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "packages", "backend-core")))

from app.core.unit_of_work import APIUnitOfWork
from app.modules.ai.service import AIService
from app.modules.ai.schemas import TriageSessionCreate, SymptomAssessmentCreate
from app.modules.vitals.service import VitalsService
from app.modules.vitals.schemas import VitalIngest
from database.models import Profile, Organization, Clinic, Doctor, Patient, MeasurementType

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
        # Create test organization
        org = Organization(id=org_id, name="AI Analytics Test Hospital", status="active")
        uow.session.add(org)
        
        # Create Doctor Profile & Entity
        doc_email = f"doc.ai.{uuid.uuid4().hex[:6]}@test.com"
        doc_profile = Profile(id=doc_id, email=doc_email, first_name="Doc", last_name="AI")
        uow.session.add(doc_profile)
        await uow.flush()
        
        doctor = Doctor(
            id=doc_id,
            organization_id=org_id,
            specialty="Cardiology",
            license_number=f"LIC-AI-{uuid.uuid4().hex[:6]}",
            timezone="UTC",
            accepting_patients=True
        )
        uow.session.add(doctor)
        
        # Create Patient Profile & Entity
        pat_email = f"patient.ai.{uuid.uuid4().hex[:6]}@test.com"
        pat_profile = Profile(id=pat_id, email=pat_email, first_name="Pat", last_name="AI")
        uow.session.add(pat_profile)
        await uow.flush()
        
        patient = Patient(
            id=pat_id,
            organization_id=org_id,
            mrn=f"MRN-AI-{uuid.uuid4().hex[:6]}",
            primary_doctor_id=doc_id,
            status="active"
        )
        uow.session.add(patient)
        
        # Insert heart rate type if not exists
        query_m = select(MeasurementType).filter(MeasurementType.code == "LOINC-8867-4")
        res_m = await uow.session.execute(query_m)
        m_type = res_m.scalars().first()
        if not m_type:
            m_type = MeasurementType(
                code="LOINC-8867-4",
                display_name="Heart Rate",
                unit="bpm",
                normal_range_low=60.0,
                normal_range_high=100.0,
                is_active=True
            )
            uow.session.add(m_type)
        await uow.flush()
        
    return {"org_id": org_id, "doctor_id": doc_id, "patient_id": pat_id}

@pytest.mark.anyio
async def test_ai_triage_and_risk_scoring(test_session, test_data):
    uow = APIUnitOfWork(test_session)
    service = AIService(uow)
    vitals_service = VitalsService(uow)
    
    pat_id = test_data["patient_id"]
    doc_id = test_data["doctor_id"]
    
    # 1. Test AI Symptom Triage (Emergency keyword trigger)
    triage_in = TriageSessionCreate(
        symptoms=[
            SymptomAssessmentCreate(symptom="Severe chest pressure pain", duration="2 hours", notes="Radiating to arm")
        ]
    )
    async with uow:
        triage = await service.create_triage_session(
            patient_id=pat_id,
            obj_in=triage_in,
            actor_id=pat_id
        )
        assert triage.urgency == "critical"
        assert "ER" in triage.recommended_action
        assert len(triage.symptoms) == 1

    # 2. Test AI Symptom Triage (Routine cold scenario)
    triage_routine_in = TriageSessionCreate(
        symptoms=[
            SymptomAssessmentCreate(symptom="Mild runny nose", duration="3 days")
        ]
    )
    async with uow:
        triage_r = await service.create_triage_session(
            patient_id=pat_id,
            obj_in=triage_routine_in,
            actor_id=pat_id
        )
        assert triage_r.urgency == "routine"
        assert "telehealth" in triage_r.recommended_action

    # 3. Test AI Clinical Risk Scoring (Based on abnormal heart rate vitals)
    # First ingest high heart rate vitals
    vital_in = VitalIngest(
        measurement_code="LOINC-8867-4",
        value_numeric=112.0, # High heart rate avg
        recorded_at=datetime.now(timezone.utc),
        source="wearable"
    )
    async with uow:
        await vitals_service.ingest_vital(
            patient_id=pat_id,
            obj_in=vital_in,
            actor_id=doc_id
        )
        
    # Trigger prediction
    async with uow:
        prediction = await service.generate_clinical_risk_prediction(
            patient_id=pat_id,
            prediction_type="cardiovascular",
            actor_id=doc_id
        )
        assert prediction.score == 75.0
        assert prediction.provider == "gemini"
        assert "cardiac strain" in prediction.confidence_reason
