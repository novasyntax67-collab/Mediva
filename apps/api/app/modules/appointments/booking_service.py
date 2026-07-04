from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.future import select
import uuid
import sys
import os

# Ensure backend-core is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages", "backend-core")))

from app.core.unit_of_work import APIUnitOfWork
from app.modules.appointments.availability_service import AvailabilityService
from database.models import Appointment, AppointmentParticipant, Doctor, Patient, AuditLog
from events.events import appointment_created

class AppointmentBookingService:
    def __init__(self, uow: APIUnitOfWork):
        self.uow = uow
        self.availability_service = AvailabilityService(uow)

    async def book_appointment(
        self,
        patient_id: uuid.UUID,
        doctor_id: uuid.UUID,
        clinic_id: uuid.UUID,
        scheduled_time: datetime,
        duration_minutes: int,
        reason: Optional[str] = None,
        actor_id: Optional[uuid.UUID] = None
    ) -> Appointment:
        """
        Main transactional engine to book an appointment.
        Uses Row-Level Locking (FOR UPDATE) to prevent double-booking race conditions.
        """
        # 1. Acquire Row-Level Lock on Doctor to block concurrent schedules for this provider
        query_doc = select(Doctor).filter(Doctor.id == doctor_id).with_for_update()
        res_doc = await self.uow.session.execute(query_doc)
        doctor = res_doc.scalars().first()
        
        if not doctor or not doctor.accepting_patients or doctor.deleted_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Clinician is not active or not accepting new bookings."
            )

        # 2. Fetch and validate Patient
        patient = await self.uow.session.get(Patient, patient_id)
        if not patient or patient.status != "active" or patient.deleted_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient account is not active."
            )

        # 3. Prevent booking in the past
        # Scheduled time must be in the future
        now_utc = datetime.now(scheduled_time.tzinfo) if scheduled_time.tzinfo else datetime.utcnow()
        if scheduled_time < now_utc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot book appointments in the past."
            )

        # 4. Check slot availability
        available_slots = await self.availability_service.get_available_slots(doctor_id, scheduled_time.date(), duration_minutes)
        slot_iso = scheduled_time.isoformat()
        
        # Verify requested scheduled_time falls on an available start time
        is_available = any(slot["start_time"] == slot_iso for slot in available_slots)
        if not is_available:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The requested slot is already booked or falls outside working hours."
            )

        # 5. Create Appointment Record
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            clinic_id=clinic_id,
            scheduled_time=scheduled_time,
            duration=duration_minutes,
            status="scheduled", # Inits with confirmed scheduled status
            booked_by=actor_id or patient_id,
            reason=reason
        )
        self.uow.session.add(appointment)
        await self.uow.session.flush()

        # 6. Add Participants
        patient_participant = AppointmentParticipant(
            appointment_id=appointment.id,
            profile_id=patient_id,
            role="patient",
            status="accepted"
        )
        doctor_participant = AppointmentParticipant(
            appointment_id=appointment.id,
            profile_id=doctor_id,
            role="doctor",
            status="accepted"
        )
        self.uow.session.add(patient_participant)
        self.uow.session.add(doctor_participant)

        # 7. Log Audit Trail
        audit = AuditLog(
            actor_id=actor_id or patient_id,
            action="APPOINTMENT_BOOK",
            entity_type="appointments",
            entity_id=appointment.id,
            new_value={"detail": f"Patient {patient_id} booked appointment with doctor {doctor_id} at {scheduled_time}"}
        )
        self.uow.session.add(audit)

        # 8. Collect domain event (persisted in outbox atomically on commit)
        self.uow.collect_event(
            appointment_created(
                appointment_id=str(appointment.id),
                patient_id=str(patient_id),
                doctor_id=str(doctor_id),
                clinic_id=str(clinic_id),
                scheduled_time=scheduled_time.isoformat(),
                duration_minutes=duration_minutes,
                actor_id=str(actor_id or patient_id),
                tenant_id=str(patient.organization_id) if patient.organization_id else None,
            )
        )
        
        # 9. Return created appointment. 
        # API router context will commit transaction on success, or rollback on failure.
        return appointment

