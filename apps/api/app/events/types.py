"""
Domain Event type definitions and factory functions.

Re-exports all typed event factories from the shared backend-core package.
Services call these factories via `from app.events.types import appointment_created`.
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages", "backend-core")))

from events.events import (
    appointment_created,
    appointment_cancelled,
    appointment_rescheduled,
    consultation_started,
    consultation_completed,
    prescription_created,
    vital_recorded,
    risk_generated,
)

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

__all__ = [
    # Factories
    "appointment_created",
    "appointment_cancelled",
    "appointment_rescheduled",
    "consultation_started",
    "consultation_completed",
    "prescription_created",
    "vital_recorded",
    "risk_generated",
    # Payload models
    "AppointmentCreatedPayload",
    "AppointmentCancelledPayload",
    "AppointmentRescheduledPayload",
    "ConsultationStartedPayload",
    "ConsultationCompletedPayload",
    "PrescriptionCreatedPayload",
    "VitalRecordedPayload",
    "RiskGeneratedPayload",
]
