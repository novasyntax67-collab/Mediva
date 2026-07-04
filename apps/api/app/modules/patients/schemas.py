from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from decimal import Decimal
import uuid

class PatientBase(BaseModel):
    mrn: str
    organization_id: uuid.UUID
    primary_doctor_id: Optional[uuid.UUID] = None
    status: str = "active"
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    height: Optional[Decimal] = None
    weight: Optional[Decimal] = None
    preferred_language: str = "en"
    photo_url: Optional[str] = None
    deceased_at: Optional[datetime] = None

class PatientCreate(PatientBase):
    id: uuid.UUID # References profile.id

class PatientUpdate(BaseModel):
    primary_doctor_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    height: Optional[Decimal] = None
    weight: Optional[Decimal] = None
    preferred_language: Optional[str] = None
    photo_url: Optional[str] = None
    deceased_at: Optional[datetime] = None

class PatientInDB(PatientBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
