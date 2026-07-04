from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid

class ConsultationBase(BaseModel):
    appointment_id: uuid.UUID
    chief_complaint: Optional[str] = None
    soap_notes: Optional[Dict[str, Any]] = None # Subjective, Objective, Assessment, Plan
    summary: Optional[str] = None
    follow_up: Optional[str] = None

class ConsultationCreate(ConsultationBase):
    pass

class ConsultationUpdate(BaseModel):
    chief_complaint: Optional[str] = None
    soap_notes: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    follow_up: Optional[str] = None

class ConsultationDiagnosisCreate(BaseModel):
    condition_code: str
    name: str
    category: str = "primary" # primary, secondary
    status: str = "active" # active, resolved

class ConsultationDiagnosisInDB(ConsultationDiagnosisCreate):
    id: uuid.UUID
    consultation_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class ConsultationInDB(ConsultationBase):
    room_id: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    diagnoses: List[ConsultationDiagnosisInDB] = []

    class Config:
        from_attributes = True

class TelehealthSessionResponse(BaseModel):
    appointment_id: uuid.UUID
    room_id: str
    token: str
    livekit_url: str
