from fastapi import APIRouter, Depends, status, Query
from app.core.dependencies import get_uow, get_current_user, require_permission
from app.core.unit_of_work import APIUnitOfWork
from app.modules.consultation.schemas import (
    ConsultationCreate, ConsultationUpdate, ConsultationDiagnosisCreate, 
    ConsultationInDB, ConsultationDiagnosisInDB, TelehealthSessionResponse
)
from app.modules.consultation.service import ConsultationService
import uuid

router = APIRouter(prefix="/consultations", tags=["consultations"])

@router.post("/{appointment_id}/start", response_model=TelehealthSessionResponse)
async def start_telehealth_consultation(
    appointment_id: uuid.UUID,
    uow: APIUnitOfWork = Depends(get_uow),
    actor_id: uuid.UUID = Depends(get_current_user),
    _ = Depends(require_permission("records:write"))
):
    async with uow:
        service = ConsultationService(uow)
        # Mock participant name since profile info query not needed for tokens
        session_info = await service.start_consultation(
            appointment_id=appointment_id,
            actor_id=actor_id,
            actor_name="Dr. Jane Doe"
        )
    return session_info

@router.get("/{appointment_id}", response_model=ConsultationInDB)
async def get_consultation_encounter(
    appointment_id: uuid.UUID,
    uow: APIUnitOfWork = Depends(get_uow)
):
    async with uow:
        service = ConsultationService(uow)
        return await service.get_consultation(appointment_id)

@router.patch("/{appointment_id}", response_model=ConsultationInDB)
async def update_consultation_notes(
    appointment_id: uuid.UUID,
    obj_in: ConsultationUpdate,
    uow: APIUnitOfWork = Depends(get_uow),
    actor_id: uuid.UUID = Depends(get_current_user),
    _ = Depends(require_permission("records:write"))
):
    async with uow:
        service = ConsultationService(uow)
        return await service.update_consultation(
            appointment_id=appointment_id,
            obj_in=obj_in,
            actor_id=actor_id
        )

@router.post("/{appointment_id}/diagnoses", response_model=ConsultationDiagnosisInDB, status_code=status.HTTP_201_CREATED)
async def add_consultation_diagnosis(
    appointment_id: uuid.UUID,
    obj_in: ConsultationDiagnosisCreate,
    uow: APIUnitOfWork = Depends(get_uow),
    actor_id: uuid.UUID = Depends(get_current_user),
    _ = Depends(require_permission("records:write"))
):
    async with uow:
        service = ConsultationService(uow)
        return await service.add_diagnosis(
            appointment_id=appointment_id,
            obj_in=obj_in,
            actor_id=actor_id
        )

@router.post("/{appointment_id}/complete", response_model=ConsultationInDB)
async def complete_consultation_session(
    appointment_id: uuid.UUID,
    uow: APIUnitOfWork = Depends(get_uow),
    actor_id: uuid.UUID = Depends(get_current_user),
    _ = Depends(require_permission("records:write"))
):
    async with uow:
        service = ConsultationService(uow)
        return await service.complete_consultation(
            appointment_id=appointment_id,
            actor_id=actor_id
        )
