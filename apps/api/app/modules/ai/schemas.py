from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

class SymptomAssessmentCreate(BaseModel):
    symptom: str
    duration: Optional[str] = None
    notes: Optional[str] = None

class TriageSessionCreate(BaseModel):
    symptoms: List[SymptomAssessmentCreate]

class SymptomAssessmentInDB(SymptomAssessmentCreate):
    id: uuid.UUID
    triage_session_id: uuid.UUID

    class Config:
        from_attributes = True

class TriageSessionInDB(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    started_at: datetime
    urgency: Optional[str] = None
    recommended_action: Optional[str] = None
    escalated: bool
    escalated_to: Optional[uuid.UUID] = None
    guideline_reference: Optional[str] = None
    symptoms: List[SymptomAssessmentInDB] = []

    class Config:
        from_attributes = True

class AIPredictionCreate(BaseModel):
    prediction_type: str

class AIPredictionInDB(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    type: str
    score: float
    feature_importance: Optional[Dict[str, Any]] = None
    action_taken: Optional[str] = None
    model_version: str
    prompt_version: Optional[str] = None
    confidence_reason: Optional[str] = None
    reviewed_by_clinician: bool
    provider: Optional[str] = None
    model_name: Optional[str] = None
    latency_ms: Optional[int] = None
    token_usage: Optional[Dict[str, Any]] = None
    cost: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True
