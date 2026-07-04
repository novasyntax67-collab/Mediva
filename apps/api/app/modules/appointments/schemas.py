from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid

class AppointmentBase(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    clinic_id: uuid.UUID
    scheduled_time: datetime
    duration_minutes: int = 30
    reason: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    status: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    reason: Optional[str] = None

class AppointmentInDB(AppointmentBase):
    id: uuid.UUID
    status: str
    booked_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
