"""
Domain Event factory functions.

Each factory constructs a fully-typed DomainEvent with a validated Pydantic
payload. Services call these instead of constructing DomainEvent directly.
"""
from events.base import DomainEvent
from events.payloads import (
    AppointmentCreatedPayload,
    AppointmentCancelledPayload,
    AppointmentRescheduledPayload,
    ConsultationStartedPayload,
    ConsultationCompletedPayload,
    PrescriptionCreatedPayload,
    VitalRecordedPayload,
    RiskGeneratedPayload,
)
from typing import Optional


# ─── Appointment Events ──────────────────────────────────────────────────────

def appointment_created(
    appointment_id: str,
    patient_id: str,
    doctor_id: str,
    clinic_id: str,
    scheduled_time: str,
    duration_minutes: int,
    actor_id: str,
    tenant_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> DomainEvent:
    payload = AppointmentCreatedPayload(
        appointment_id=appointment_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        clinic_id=clinic_id,
        scheduled_time=scheduled_time,
        duration_minutes=duration_minutes,
    )
    return DomainEvent(
        event_type="appointment.created",
        aggregate_type="appointment",
        aggregate_id=appointment_id,
        actor_id=actor_id,
        payload=payload.model_dump(),
        tenant_id=tenant_id,
        correlation_id=correlation_id,
    )


def appointment_cancelled(
    appointment_id: str,
    patient_id: str,
    doctor_id: str,
    actor_id: str,
    reason: Optional[str] = None,
    tenant_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> DomainEvent:
    payload = AppointmentCancelledPayload(
        appointment_id=appointment_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        reason=reason,
    )
    return DomainEvent(
        event_type="appointment.cancelled",
        aggregate_type="appointment",
        aggregate_id=appointment_id,
        actor_id=actor_id,
        payload=payload.model_dump(),
        tenant_id=tenant_id,
        correlation_id=correlation_id,
    )


def appointment_rescheduled(
    appointment_id: str,
    patient_id: str,
    doctor_id: str,
    old_time: str,
    new_time: str,
    actor_id: str,
    tenant_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> DomainEvent:
    payload = AppointmentRescheduledPayload(
        appointment_id=appointment_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        old_time=old_time,
        new_time=new_time,
    )
    return DomainEvent(
        event_type="appointment.rescheduled",
        aggregate_type="appointment",
        aggregate_id=appointment_id,
        actor_id=actor_id,
        payload=payload.model_dump(),
        tenant_id=tenant_id,
        correlation_id=correlation_id,
    )


# ─── Consultation Events ─────────────────────────────────────────────────────

def consultation_started(
    appointment_id: str,
    doctor_id: str,
    patient_id: str,
    room_id: str,
    actor_id: str,
    tenant_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> DomainEvent:
    payload = ConsultationStartedPayload(
        appointment_id=appointment_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        room_id=room_id,
    )
    return DomainEvent(
        event_type="consultation.started",
        aggregate_type="consultation",
        aggregate_id=appointment_id,
        actor_id=actor_id,
        payload=payload.model_dump(),
        tenant_id=tenant_id,
        correlation_id=correlation_id,
    )


def consultation_completed(
    appointment_id: str,
    doctor_id: str,
    patient_id: str,
    actor_id: str,
    tenant_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> DomainEvent:
    payload = ConsultationCompletedPayload(
        appointment_id=appointment_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
    )
    return DomainEvent(
        event_type="consultation.completed",
        aggregate_type="consultation",
        aggregate_id=appointment_id,
        actor_id=actor_id,
        payload=payload.model_dump(),
        tenant_id=tenant_id,
        correlation_id=correlation_id,
    )


# ─── Prescription Events ─────────────────────────────────────────────────────

def prescription_created(
    prescription_id: str,
    patient_id: str,
    doctor_id: str,
    consultation_id: str,
    item_count: int,
    actor_id: str,
    tenant_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> DomainEvent:
    payload = PrescriptionCreatedPayload(
        prescription_id=prescription_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        consultation_id=consultation_id,
        item_count=item_count,
    )
    return DomainEvent(
        event_type="prescription.created",
        aggregate_type="prescription",
        aggregate_id=prescription_id,
        actor_id=actor_id,
        payload=payload.model_dump(),
        tenant_id=tenant_id,
        correlation_id=correlation_id,
    )


# ─── Vitals Events ───────────────────────────────────────────────────────────

def vital_recorded(
    vital_id: str,
    patient_id: str,
    measurement_code: str,
    value_numeric: float,
    status_val: str,
    actor_id: str,
    tenant_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> DomainEvent:
    payload = VitalRecordedPayload(
        vital_id=vital_id,
        patient_id=patient_id,
        measurement_code=measurement_code,
        value_numeric=value_numeric,
        status=status_val,
    )
    return DomainEvent(
        event_type="vital.recorded",
        aggregate_type="vital",
        aggregate_id=vital_id,
        actor_id=actor_id,
        payload=payload.model_dump(),
        tenant_id=tenant_id,
        correlation_id=correlation_id,
    )


# ─── Risk / AI Events ────────────────────────────────────────────────────────

def risk_generated(
    prediction_id: str,
    patient_id: str,
    prediction_type: str,
    score: float,
    actor_id: str,
    tenant_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> DomainEvent:
    payload = RiskGeneratedPayload(
        prediction_id=prediction_id,
        patient_id=patient_id,
        prediction_type=prediction_type,
        score=score,
    )
    return DomainEvent(
        event_type="risk.generated",
        aggregate_type="ai_prediction",
        aggregate_id=prediction_id,
        actor_id=actor_id,
        payload=payload.model_dump(),
        tenant_id=tenant_id,
        correlation_id=correlation_id,
    )
