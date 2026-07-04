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
from app.modules.vitals.service import VitalsService
from app.modules.vitals.schemas import VitalIngest
from database.models import Profile, Organization, Clinic, Doctor, Patient, MeasurementType, Device

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
        org = Organization(id=org_id, name="Vitals Test Hospital", status="active")
        uow.session.add(org)
        
        # Create Doctor Profile & Entity
        doc_email = f"doc.vitals.{uuid.uuid4().hex[:6]}@test.com"
        doc_profile = Profile(id=doc_id, email=doc_email, first_name="Doc", last_name="Vitals")
        uow.session.add(doc_profile)
        await uow.flush()
        
        doctor = Doctor(
            id=doc_id,
            organization_id=org_id,
            specialty="Cardiology",
            license_number=f"LIC-VIT-{uuid.uuid4().hex[:6]}",
            timezone="UTC",
            accepting_patients=True
        )
        uow.session.add(doctor)
        
        # Create Patient Profile & Entity
        pat_email = f"patient.vitals.{uuid.uuid4().hex[:6]}@test.com"
        pat_profile = Profile(id=pat_id, email=pat_email, first_name="Pat", last_name="Vitals")
        uow.session.add(pat_profile)
        await uow.flush()
        
        patient = Patient(
            id=pat_id,
            organization_id=org_id,
            mrn=f"MRN-VIT-{uuid.uuid4().hex[:6]}",
            primary_doctor_id=doc_id,
            status="active"
        )
        uow.session.add(patient)
        
        # Insert a specific MeasurementType with thresholds if not exists
        query_m = select(MeasurementType).filter(MeasurementType.code == "LOINC-8867-4")
        res_m = await uow.session.execute(query_m)
        m_type = res_m.scalars().first()
        if not m_type:
            m_type = MeasurementType(
                code="LOINC-8867-4", # Heart rate code
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
async def test_vitals_ingestion_timeline(test_session, test_data):
    uow = APIUnitOfWork(test_session)
    service = VitalsService(uow)
    
    pat_id = test_data["patient_id"]
    doc_id = test_data["doctor_id"]
    
    # 1. Normal Vitals Ingestion (HR = 72 bpm)
    normal_in = VitalIngest(
        measurement_code="LOINC-8867-4",
        value_numeric=72.0,
        recorded_at=datetime.now(timezone.utc),
        source="wearable",
        device_serial_number=f"SN-WEAR-{uuid.uuid4().hex[:6]}"
    )
    async with uow:
        vital_a = await service.ingest_vital(
            patient_id=pat_id,
            obj_in=normal_in,
            actor_id=doc_id
        )
        assert vital_a.status == "normal"
        assert vital_a.device_id is not None # Dynamic device registration!

    # 2. Abnormal Vitals Ingestion (HR = 110 bpm - Tachycardia alert)
    abnormal_in = VitalIngest(
        measurement_code="LOINC-8867-4",
        value_numeric=110.0,
        recorded_at=datetime.now(timezone.utc),
        source="wearable"
    )
    async with uow:
        vital_b = await service.ingest_vital(
            patient_id=pat_id,
            obj_in=abnormal_in,
            actor_id=doc_id
        )
        assert vital_b.status == "abnormal"

    # 3. Retrieve Vitals Timeline Order DESC
    async with uow:
        timeline = await service.get_vitals_timeline(
            patient_id=pat_id,
            measurement_code="LOINC-8867-4"
        )
        assert len(timeline) >= 2
        # Recorded at of first item should be greater than or equal to second
        assert timeline[0].recorded_at >= timeline[1].recorded_at
