from fastapi import APIRouter, Depends, status, Request
from typing import List
from app.core.dependencies import get_uow, get_current_user, require_permission
from app.core.unit_of_work import APIUnitOfWork
from app.modules.patients.schemas import PatientCreate, PatientUpdate, PatientInDB
from app.modules.patients.service import PatientService
from app.modules.patients.permissions import verify_patient_access
from app.modules.patients.validators import validate_birth_date
from app.modules.patients.events import emit_patient_registered_event
import uuid

router = APIRouter(prefix="/patients", tags=["patients"])

@router.post("/", response_model=PatientInDB, status_code=status.HTTP_201_CREATED)
async def register_patient(
    obj_in: PatientCreate,
    uow: APIUnitOfWork = Depends(get_uow),
    actor_id: uuid.UUID = Depends(get_current_user)
):
    if obj_in.date_of_birth:
        validate_birth_date(obj_in.date_of_birth)
    
    async with uow:
        service = PatientService(uow)
        patient = await service.register_patient(obj_in, actor_id=actor_id)
        
    await emit_patient_registered_event(patient.id)
    return patient

@router.get("/{patient_id}", response_model=PatientInDB)
async def get_patient(
    patient_id: uuid.UUID,
    request: Request,
    uow: APIUnitOfWork = Depends(get_uow)
):
    verify_patient_access(request, str(patient_id))
    async with uow:
        service = PatientService(uow)
        patient = await service.get_patient(patient_id)
    return patient

@router.patch("/{patient_id}", response_model=PatientInDB)
async def update_patient(
    patient_id: uuid.UUID,
    obj_in: PatientUpdate,
    request: Request,
    uow: APIUnitOfWork = Depends(get_uow),
    actor_id: uuid.UUID = Depends(get_current_user)
):
    verify_patient_access(request, str(patient_id))
    if obj_in.date_of_birth:
        validate_birth_date(obj_in.date_of_birth)
        
    async with uow:
        service = PatientService(uow)
        patient = await service.update_patient(patient_id, obj_in, actor_id=actor_id)
    return patient

@router.get("/", response_model=List[PatientInDB])
async def search_patients(
    query: str,
    uow: APIUnitOfWork = Depends(get_uow),
    _ = Depends(require_permission("records:read"))
):
    async with uow:
        service = PatientService(uow)
        return await service.search_patients(query)

@router.get("/{patient_id}/care-team")
async def get_patient_care_team(
    patient_id: uuid.UUID,
    request: Request,
    uow: APIUnitOfWork = Depends(get_uow)
):
    verify_patient_access(request, str(patient_id))
    async with uow:
        service = PatientService(uow)
        return await service.get_care_team(patient_id)

@router.get("/{patient_id}/timeline")
async def get_patient_timeline(
    patient_id: uuid.UUID,
    request: Request,
    limit: int = 50,
    uow: APIUnitOfWork = Depends(get_uow)
):
    verify_patient_access(request, str(patient_id))
    async with uow:
        service = PatientService(uow)
        return await service.get_patient_timeline(patient_id, limit=limit)
