"""
Typed Pydantic payload models for each domain event.

Each payload contains only lightweight IDs and essential scalar values.
Workers load full entity data from the database when they need it.
Using Pydantic gives us:
  - Schema validation at publish time
  - Serialization consistency
  - Easier versioning
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ─── Appointment ──────────────────────────────────────────────────────────────

class AppointmentCreatedPayload(BaseModel):
    appointment_id: str
    patient_id: str
    doctor_id: str
    clinic_id: str
    scheduled_time: str
    duration_minutes: int

class AppointmentCancelledPayload(BaseModel):
    appointment_id: str
    patient_id: str
    doctor_id: str
    reason: Optional[str] = None

class AppointmentRescheduledPayload(BaseModel):
    appointment_id: str
    patient_id: str
    doctor_id: str
    old_time: str
    new_time: str


# ─── Consultation ─────────────────────────────────────────────────────────────

class ConsultationStartedPayload(BaseModel):
    appointment_id: str
    doctor_id: str
    patient_id: str
    room_id: str

class ConsultationCompletedPayload(BaseModel):
    appointment_id: str
    doctor_id: str
    patient_id: str


# ─── Prescription ─────────────────────────────────────────────────────────────

class PrescriptionCreatedPayload(BaseModel):
    prescription_id: str
    patient_id: str
    doctor_id: str
    consultation_id: str
    item_count: int


# ─── Vitals ───────────────────────────────────────────────────────────────────

class VitalRecordedPayload(BaseModel):
    vital_id: str
    patient_id: str
    measurement_code: str
    value_numeric: Optional[float] = None
    status: str  # "normal" | "abnormal"


# ─── Risk / AI ────────────────────────────────────────────────────────────────

class RiskGeneratedPayload(BaseModel):
    prediction_id: str
    patient_id: str
    prediction_type: str
    score: float
