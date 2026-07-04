from fastapi import APIRouter, Depends, status
from app.core.dependencies import get_uow, get_current_user, require_permission
from app.core.unit_of_work import APIUnitOfWork
from app.modules.prescriptions.schemas import (
    PrescriptionCreate, PrescriptionInDB, MedicationAdherenceLog, MedicationAdherenceInDB
)
from app.modules.prescriptions.service import PrescriptionService
import uuid

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])

@router.post("/", response_model=PrescriptionInDB, status_code=status.HTTP_201_CREATED)
async def create_new_prescription(
    obj_in: PrescriptionCreate,
    uow: APIUnitOfWork = Depends(get_uow),
    actor_id: uuid.UUID = Depends(get_current_user),
    _ = Depends(require_permission("records:write"))
):
    async with uow:
        service = PrescriptionService(uow)
        return await service.create_prescription(
            consultation_id=obj_in.consultation_id,
            obj_in=obj_in,
            actor_id=actor_id
        )

@router.get("/{prescription_id}", response_model=PrescriptionInDB)
async def get_prescription(
    prescription_id: uuid.UUID,
    uow: APIUnitOfWork = Depends(get_uow)
):
    async with uow:
        service = PrescriptionService(uow)
        return await service.get_prescription(prescription_id)

@router.post("/adherence/{adherence_id}/log", response_model=MedicationAdherenceInDB)
async def log_medication_adherence(
    adherence_id: uuid.UUID,
    log_in: MedicationAdherenceLog,
    uow: APIUnitOfWork = Depends(get_uow),
    actor_id: uuid.UUID = Depends(get_current_user)
):
    async with uow:
        service = PrescriptionService(uow)
        return await service.log_adherence(
            adherence_id=adherence_id,
            log_in=log_in,
            actor_id=actor_id
        )
