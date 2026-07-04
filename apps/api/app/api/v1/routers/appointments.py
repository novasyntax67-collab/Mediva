from fastapi import APIRouter, Depends, status, Query
from app.core.dependencies import get_uow, get_current_user
from app.core.unit_of_work import APIUnitOfWork
from app.modules.appointments.schemas import AppointmentCreate, AppointmentInDB, AppointmentUpdate
from app.modules.appointments.service import AppointmentService
from datetime import date, datetime
from typing import List
import uuid

router = APIRouter(prefix="/appointments", tags=["appointments"])

@router.post("/", response_model=AppointmentInDB, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    obj_in: AppointmentCreate,
    uow: APIUnitOfWork = Depends(get_uow),
    actor_id: uuid.UUID = Depends(get_current_user)
):
    async with uow:
        service = AppointmentService(uow)
        appointment = await service.booking_service.book_appointment(
            patient_id=obj_in.patient_id,
            doctor_id=obj_in.doctor_id,
            clinic_id=obj_in.clinic_id,
            scheduled_time=obj_in.scheduled_time,
            duration_minutes=obj_in.duration_minutes,
            reason=obj_in.reason,
            actor_id=actor_id
        )
    return appointment

@router.get("/{appointment_id}", response_model=AppointmentInDB)
async def get_appointment(
    appointment_id: uuid.UUID,
    uow: APIUnitOfWork = Depends(get_uow)
):
    async with uow:
        service = AppointmentService(uow)
        return await service.get_appointment(appointment_id)

@router.patch("/{appointment_id}/reschedule", response_model=AppointmentInDB)
async def reschedule_appointment(
    appointment_id: uuid.UUID,
    new_time: datetime,
    uow: APIUnitOfWork = Depends(get_uow),
    actor_id: uuid.UUID = Depends(get_current_user)
):
    async with uow:
        service = AppointmentService(uow)
        return await service.reschedule_appointment(
            appointment_id=appointment_id,
            new_time=new_time,
            actor_id=actor_id
        )

@router.delete("/{appointment_id}", response_model=AppointmentInDB)
async def cancel_appointment(
    appointment_id: uuid.UUID,
    uow: APIUnitOfWork = Depends(get_uow),
    actor_id: uuid.UUID = Depends(get_current_user)
):
    async with uow:
        service = AppointmentService(uow)
        return await service.cancel_appointment(appointment_id, actor_id=actor_id)

@router.get("/doctors/{doctor_id}/availability")
async def get_doctor_availability(
    doctor_id: uuid.UUID,
    target_date: date = Query(..., description="Target date for available slots"),
    duration_minutes: int = Query(30, description="Slot duration in minutes"),
    uow: APIUnitOfWork = Depends(get_uow)
):
    async with uow:
        service = AppointmentService(uow)
        return await service.availability_service.get_available_slots(
            doctor_id=doctor_id,
            target_date=target_date,
            slot_duration_minutes=duration_minutes
        )
