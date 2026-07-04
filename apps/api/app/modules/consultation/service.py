from app.core.unit_of_work import APIUnitOfWork
from app.modules.consultation.schemas import ConsultationCreate, ConsultationUpdate, ConsultationDiagnosisCreate
from app.core.config import settings
from sqlalchemy.future import select
from database.models import Consultation, ConsultationDiagnosis, Appointment, AuditLog, Condition
from fastapi import HTTPException, status
from datetime import datetime
import uuid
import sys
import os

# Ensure backend-core is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages", "backend-core")))

from telehealth.livekit import LiveKitTokenGenerator
from events.events import consultation_started, consultation_completed

class ConsultationService:
    def __init__(self, uow: APIUnitOfWork):
        self.uow = uow
        self.lk_generator = LiveKitTokenGenerator(
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET
        )

    async def get_consultation(self, appointment_id: uuid.UUID) -> Consultation:
        consult = await self.uow.consultations.get_by_appointment(appointment_id)
        if not consult:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation has not been initialized for this appointment."
            )
        return consult

    async def start_consultation(
        self, appointment_id: uuid.UUID, actor_id: uuid.UUID, actor_name: str
    ) -> dict:
        """
        Starts a clinical consultation. Creates room_id and generates LiveKit join token.
        """
        # 1. Fetch appointment details
        appointment = await self.uow.appointments.get(appointment_id)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target appointment not found."
            )

        if appointment.status == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot start consultation for a cancelled appointment."
            )

        # 2. Retrieve or create consultation session
        consult = await self.uow.consultations.get_by_appointment(appointment_id)
        room_name = f"room-{appointment_id}"
        
        if not consult:
            consult = Consultation(
                appointment_id=appointment_id,
                room_id=room_name,
                status="in_progress",
                started_at=datetime.utcnow()
            )
            self.uow.session.add(consult)
            
            # Transition appointment status to checked_in / in_consultation
            appointment.status = "in_consultation"
            self.uow.session.add(appointment)
            
            # Log transition in AuditLog
            audit = AuditLog(
                actor_id=actor_id,
                action="CONSULTATION_START",
                entity_type="consultations",
                entity_id=appointment_id,
                new_value={"detail": f"Consultation started by doctor {actor_id}"}
            )
            self.uow.session.add(audit)

            # Collect domain event
            self.uow.collect_event(
                consultation_started(
                    appointment_id=str(appointment_id),
                    doctor_id=str(actor_id),
                    patient_id=str(appointment.patient_id),
                    room_id=room_name,
                    actor_id=str(actor_id),
                )
            )
            await self.uow.flush()

        # 3. Generate LiveKit Access Token
        token = self.lk_generator.generate_token(
            room_name=room_name,
            participant_identity=str(actor_id),
            participant_name=actor_name
        )

        return {
            "appointment_id": appointment_id,
            "room_id": room_name,
            "token": token,
            "livekit_url": settings.LIVEKIT_URL
        }

    async def update_consultation(
        self, appointment_id: uuid.UUID, obj_in: ConsultationUpdate, actor_id: uuid.UUID
    ) -> Consultation:
        consult = await self.get_consultation(appointment_id)
        
        # Enforce immutability
        if consult.status == "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify a completed consultation."
            )

        update_data = obj_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(consult, key, value)
            
        self.uow.session.add(consult)

        # Log transition
        audit = AuditLog(
            actor_id=actor_id,
            action="CONSULTATION_UPDATE",
            entity_type="consultations",
            entity_id=appointment_id,
            new_value={"detail": "Updated SOAP notes and summary details"}
        )
        self.uow.session.add(audit)
        return consult

    async def add_diagnosis(
        self, appointment_id: uuid.UUID, obj_in: ConsultationDiagnosisCreate, actor_id: uuid.UUID
    ) -> ConsultationDiagnosis:
        consult = await self.get_consultation(appointment_id)
        if consult.status == "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add diagnosis to a completed consultation."
            )

        # 1. Fetch or dynamically register Condition in dict
        query_cond = select(Condition).filter(
            Condition.code == obj_in.condition_code,
            Condition.code_system == "ICD-10",
            Condition.deleted_at == None
        )
        res_cond = await self.uow.session.execute(query_cond)
        condition = res_cond.scalars().first()
        
        if not condition:
            condition = Condition(
                code_system="ICD-10",
                code=obj_in.condition_code,
                display=obj_in.name
            )
            self.uow.session.add(condition)
            await self.uow.flush()

        # 2. Map and insert ConsultationDiagnosis
        diagnosis = ConsultationDiagnosis(
            consultation_id=appointment_id,
            condition_id=condition.id,
            is_primary=(obj_in.category == "primary"),
            notes=f"Status: {obj_in.status}"
        )
        self.uow.session.add(diagnosis)
        await self.uow.flush()
        
        # 3. Dynamic attributes attachment to satisfy Pydantic response models
        diagnosis.condition_code = condition.code
        diagnosis.name = condition.display
        diagnosis.category = "primary" if diagnosis.is_primary else "secondary"
        diagnosis.status = obj_in.status

        # Log transition
        audit = AuditLog(
            actor_id=actor_id,
            action="DIAGNOSIS_ADD",
            entity_type="consultation_diagnoses",
            entity_id=appointment_id,
            new_value={"detail": f"Added diagnosis {obj_in.name} ({obj_in.condition_code})"}
        )
        self.uow.session.add(audit)
        await self.uow.flush()
        return diagnosis

    async def complete_consultation(self, appointment_id: uuid.UUID, actor_id: uuid.UUID) -> Consultation:
        consult = await self.get_consultation(appointment_id)
        if consult.status == "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Consultation is already completed."
            )

        # Complete consultation
        consult.status = "completed"
        consult.ended_at = datetime.utcnow()
        self.uow.session.add(consult)

        # Update appointment status to completed
        appointment = await self.uow.appointments.get(appointment_id)
        if appointment:
            appointment.status = "completed"
            self.uow.session.add(appointment)

        # Log transition
        audit = AuditLog(
            actor_id=actor_id,
            action="CONSULTATION_COMPLETE",
            entity_type="consultations",
            entity_id=appointment_id,
            new_value={"detail": f"Completed consultation by doctor {actor_id}"}
        )
        self.uow.session.add(audit)

        # Collect domain event
        self.uow.collect_event(
            consultation_completed(
                appointment_id=str(appointment_id),
                doctor_id=str(actor_id),
                patient_id=str(appointment.patient_id) if appointment else str(actor_id),
                actor_id=str(actor_id),
            )
        )
        return consult
