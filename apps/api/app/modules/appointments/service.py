from app.core.unit_of_work import APIUnitOfWork
from app.modules.appointments.schemas import AppointmentUpdate
from app.modules.appointments.booking_service import AppointmentBookingService
from app.modules.appointments.availability_service import AvailabilityService
from database.models import Appointment, AuditLog
from fastapi import HTTPException, status
from datetime import datetime
import uuid

class AppointmentService:
    def __init__(self, uow: APIUnitOfWork):
        self.uow = uow
        self.booking_service = AppointmentBookingService(uow)
        self.availability_service = AvailabilityService(uow)

    async def get_appointment(self, appointment_id: uuid.UUID) -> Appointment:
        appt = await self.uow.appointments.get(appointment_id)
        if not appt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found."
            )
        return appt

    async def reschedule_appointment(
        self, appointment_id: uuid.UUID, new_time: datetime, actor_id: uuid.UUID
    ) -> Appointment:
        appt = await self.get_appointment(appointment_id)
        if appt.status in ("cancelled", "completed"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reschedule a {appt.status} appointment."
            )

        # Validate slot availability for the new time
        available_slots = await self.availability_service.get_available_slots(
            appt.doctor_id, new_time.date(), appt.duration
        )
        slot_iso = new_time.isoformat()
        is_available = any(slot["start_time"] == slot_iso for slot in available_slots)
        if not is_available:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The requested slot is already booked or falls outside working hours."
            )

        old_time = appt.scheduled_time
        # Perform update
        appt.scheduled_time = new_time
        self.uow.session.add(appt)

        # Log transition in AuditLog
        audit = AuditLog(
            actor_id=actor_id,
            action="APPOINTMENT_RESCHEDULE",
            entity_type="appointments",
            entity_id=appt.id,
            new_value={"detail": f"Rescheduled appointment from {old_time} to {new_time}"}
        )
        self.uow.session.add(audit)
        return appt

    async def cancel_appointment(self, appointment_id: uuid.UUID, actor_id: uuid.UUID) -> Appointment:
        appt = await self.get_appointment(appointment_id)
        if appt.status in ("cancelled", "completed"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel a {appt.status} appointment."
            )

        old_status = appt.status
        appt.status = "cancelled"
        self.uow.session.add(appt)

        # Log transition in AuditLog
        audit = AuditLog(
            actor_id=actor_id,
            action="APPOINTMENT_CANCEL",
            entity_type="appointments",
            entity_id=appt.id,
            new_value={"detail": f"Cancelled appointment (previous status: {old_status})"}
        )
        self.uow.session.add(audit)
        return appt
