import pytest
import asyncio
import uuid
import sys
import os
from datetime import date

# Add apps/api to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "packages", "backend-core")))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.unit_of_work import APIUnitOfWork
from app.modules.patients.schemas import PatientCreate, PatientUpdate
from app.modules.patients.service import PatientService
from database.models import Patient, Profile, Organization

# Local test database URL
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

@pytest.mark.anyio
async def test_patient_crud_and_service(test_session):
    uow = APIUnitOfWork(test_session)
    service = PatientService(uow)
    
    # 1. Create a dummy organization and profile for testing
    org_id = uuid.uuid4()
    profile_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    
    async with uow:
        # Create test organization
        org = Organization(id=org_id, name="Test Seeding Hospital", status="active")
        uow.session.add(org)
        
        # Create test profile
        profile = Profile(
            id=profile_id,
            email=f"test.patient.{uuid.uuid4().hex[:6]}@example.com",
            first_name="John",
            last_name="Test"
        )
        uow.session.add(profile)
        await uow.flush()
        
    # 2. Register Patient via Service Layer (Atomic block)
    patient_in = PatientCreate(
        id=profile_id,
        mrn=f"MRN-TEST-{uuid.uuid4().hex[:6]}",
        organization_id=org_id,
        status="active",
        date_of_birth=date(1990, 1, 1),
        gender="male",
        blood_group="O+",
        height=175.0,
        weight=70.0
    )
    
    async with uow:
        patient = await service.register_patient(patient_in, actor_id=actor_id)
        assert patient.id == profile_id
        assert patient.mrn == patient_in.mrn
        
    # 3. View Patient
    async with uow:
        fetched_patient = await service.get_patient(profile_id)
        assert fetched_patient is not None
        assert fetched_patient.mrn == patient_in.mrn
        
    # 4. Update Patient
    update_in = PatientUpdate(gender="female", height=176.0)
    async with uow:
        updated_patient = await service.update_patient(profile_id, update_in, actor_id=actor_id)
        assert updated_patient.gender == "female"
        assert updated_patient.height == 176.0
        
    # 5. Search Patients
    async with uow:
        results = await service.search_patients("John")
        assert len(results) >= 1
        assert any(r.id == profile_id for r in results)
