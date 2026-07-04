from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import uuid

class PrescriptionItemCreate(BaseModel):
    medication_name: str
    medication_code: Optional[str] = None # RxNorm
    dosage_quantity: float
    dosage_unit: str
    frequency_interval: int # e.g. 12
    frequency_period: str # e.g. "hour", "day"
    duration_days: int
    quantity: int
    refills: int = 0
    instructions: Optional[str] = None

class PrescriptionCreate(BaseModel):
    consultation_id: uuid.UUID
    items: List[PrescriptionItemCreate]

class PrescriptionItemInDB(BaseModel):
    id: uuid.UUID
    prescription_id: uuid.UUID
    medication_id: uuid.UUID
    dosage_quantity: float
    dosage_unit: str
    frequency_interval: int
    frequency_period: str
    duration_days: int
    quantity: int
    refills: int
    instructions: Optional[str] = None

    class Config:
        from_attributes = True

class PrescriptionInDB(BaseModel):
    id: uuid.UUID
    consultation_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    status: str
    items: List[PrescriptionItemInDB] = []
    created_at: datetime

    class Config:
        from_attributes = True

class MedicationAdherenceLog(BaseModel):
    status: str = "taken" # taken, missed, skipped
    source: str = "patient" # patient, caregiver, wearable

class MedicationAdherenceInDB(BaseModel):
    id: uuid.UUID
    prescription_item_id: uuid.UUID
    patient_id: uuid.UUID
    scheduled_time: datetime
    logged_time: Optional[datetime] = None
    status: str
    logged_by: Optional[uuid.UUID] = None
    source: str

    class Config:
        from_attributes = True
