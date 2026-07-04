from fastapi import APIRouter, Depends, status, Query
from app.core.dependencies import get_uow, get_current_user, require_permission
from app.core.unit_of_work import APIUnitOfWork
from app.modules.ai.schemas import TriageSessionCreate, TriageSessionInDB, AIPredictionCreate, AIPredictionInDB
from app.modules.ai.service import AIService
import uuid

router = APIRouter(prefix="/ai", tags=["ai"])

@router.post("/triage/patients/{patient_id}", response_model=TriageSessionInDB, status_code=status.HTTP_201_CREATED)
async def create_triage_session(
    patient_id: uuid.UUID,
    obj_in: TriageSessionCreate,
    uow: APIUnitOfWork = Depends(get_uow),
    actor_id: uuid.UUID = Depends(get_current_user)
):
    async with uow:
        service = AIService(uow)
        return await service.create_triage_session(
            patient_id=patient_id,
            obj_in=obj_in,
            actor_id=actor_id
        )

@router.post("/predictions/patients/{patient_id}", response_model=AIPredictionInDB, status_code=status.HTTP_201_CREATED)
async def trigger_clinical_risk_prediction(
    patient_id: uuid.UUID,
    obj_in: AIPredictionCreate,
    uow: APIUnitOfWork = Depends(get_uow),
    actor_id: uuid.UUID = Depends(get_current_user),
    _ = Depends(require_permission("records:write"))
):
    async with uow:
        service = AIService(uow)
        return await service.generate_clinical_risk_prediction(
            patient_id=patient_id,
            prediction_type=obj_in.prediction_type,
            actor_id=actor_id
        )
