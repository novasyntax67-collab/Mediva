from fastapi import APIRouter, Depends, status, Query
from app.core.dependencies import get_uow, get_current_user, require_permission
from app.core.unit_of_work import APIUnitOfWork
from app.modules.vitals.schemas import VitalIngest, VitalInDB
from app.modules.vitals.service import VitalsService
from typing import List
import uuid

router = APIRouter(prefix="/vitals", tags=["vitals"])

@router.post("/patients/{patient_id}", response_model=VitalInDB, status_code=status.HTTP_201_CREATED)
async def ingest_patient_vital(
    patient_id: uuid.UUID,
    obj_in: VitalIngest,
    uow: APIUnitOfWork = Depends(get_uow),
    actor_id: uuid.UUID = Depends(get_current_user),
    _ = Depends(require_permission("records:write"))
):
    async with uow:
        service = VitalsService(uow)
        return await service.ingest_vital(
            patient_id=patient_id,
            obj_in=obj_in,
            actor_id=actor_id
        )

@router.get("/patients/{patient_id}", response_model=List[VitalInDB])
async def get_patient_vitals_timeline(
    patient_id: uuid.UUID,
    measurement_code: str = Query(..., description="Measurement LOINC/dict code to fetch"),
    limit: int = Query(50, description="Timeline limits"),
    uow: APIUnitOfWork = Depends(get_uow),
    _ = Depends(require_permission("records:read"))
):
    async with uow:
        service = VitalsService(uow)
        return await service.get_vitals_timeline(
            patient_id=patient_id,
            measurement_code=measurement_code,
            limit=limit
        )
