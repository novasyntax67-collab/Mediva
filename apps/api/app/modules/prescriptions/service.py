from app.core.unit_of_work import APIUnitOfWork
from app.modules.prescriptions.schemas import PrescriptionCreate, MedicationAdherenceLog
from database.models import Medication, Prescription, PrescriptionItem, MedicationAdherence, Consultation, Appointment, AuditLog
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from sqlalchemy.future import select
import uuid
import sys
import os

# Ensure backend-core is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages", "backend-core")))

from events.events import prescription_created

class PrescriptionService:
    def __init__(self, uow: APIUnitOfWork):
        self.uow = uow

    async def create_prescription(
        self, consultation_id: uuid.UUID, obj_in: PrescriptionCreate, actor_id: uuid.UUID
    ) -> Prescription:
        """
        Creates a new prescription and registers any new medications.

        Adherence schedule generation has been moved to the Reminder Worker.
        When this transaction commits, a `prescription.created` event is persisted
        in the outbox. The Outbox Publisher dispatches it to the Reminder Worker,
        which generates the compliance calendar asynchronously. The doctor no
        longer waits for schedule prepopulation.
        """
        # 1. Fetch Consultation and related Appointment to resolve doctor and patient
        consultation = await self.uow.consultations.get_by_appointment(consultation_id)
        if not consultation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found."
            )

        appointment = await self.uow.appointments.get(consultation_id)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation appointment not found."
            )

        patient_id = appointment.patient_id
        doctor_id = appointment.doctor_id

        # 2. Insert Prescription Record
        prescription = Prescription(
            consultation_id=consultation_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
            status="active"
        )
        self.uow.session.add(prescription)
        await self.uow.flush()

        # 3. Process Prescription Items
        for item in obj_in.items:
            # Check if medication exists, or register it
            query_med = select(Medication).filter(
                Medication.name.ilike(item.medication_name),
                Medication.deleted_at == None
            )
            res_med = await self.uow.session.execute(query_med)
            medication = res_med.scalars().first()

            if not medication:
                medication = Medication(
                    name=item.medication_name,
                    code=item.medication_code
                )
                self.uow.session.add(medication)
                await self.uow.flush()

            # Insert PrescriptionItem
            p_item = PrescriptionItem(
                prescription_id=prescription.id,
                medication_id=medication.id,
                dosage_quantity=item.dosage_quantity,
                dosage_unit=item.dosage_unit,
                frequency_interval=item.frequency_interval,
                frequency_period=item.frequency_period,
                duration_days=item.duration_days,
                quantity=item.quantity,
                refills=item.refills,
                instructions=item.instructions
            )
            self.uow.session.add(p_item)
            await self.uow.flush()

        # 4. Log audit trail
        audit = AuditLog(
            actor_id=actor_id,
            action="PRESCRIPTION_CREATE",
            entity_type="prescriptions",
            entity_id=prescription.id,
            new_value={"detail": f"Doctor {doctor_id} created prescription with {len(obj_in.items)} items"}
        )
        self.uow.session.add(audit)
        await self.uow.flush()

        # 5. Collect domain event — Reminder Worker generates adherence schedule
        self.uow.collect_event(
            prescription_created(
                prescription_id=str(prescription.id),
                patient_id=str(patient_id),
                doctor_id=str(doctor_id),
                consultation_id=str(consultation_id),
                item_count=len(obj_in.items),
                actor_id=str(actor_id),
            )
        )
        
        # Populate items list relation for schema serialization
        prescription.items = await self.get_prescription_items(prescription.id)
        return prescription

    async def get_prescription_items(self, prescription_id: uuid.UUID):
        query_items = select(PrescriptionItem).filter(
            PrescriptionItem.prescription_id == prescription_id,
            PrescriptionItem.deleted_at == None
        )
        res_items = await self.uow.session.execute(query_items)
        return list(res_items.scalars().all())

    async def get_prescription(self, prescription_id: uuid.UUID) -> Prescription:
        query_p = select(Prescription).filter(
            Prescription.id == prescription_id,
            Prescription.deleted_at == None
        )
        res_p = await self.uow.session.execute(query_p)
        prescription = res_p.scalars().first()
        if not prescription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescription not found."
            )
        prescription.items = await self.get_prescription_items(prescription.id)
        return prescription

    async def log_adherence(
        self, adherence_id: uuid.UUID, log_in: MedicationAdherenceLog, actor_id: uuid.UUID
    ) -> MedicationAdherence:
        """Logs patient compliance tracking record."""
        adherence = await self.uow.session.get(MedicationAdherence, adherence_id)
        if not adherence or adherence.deleted_at:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Adherence schedule record not found."
            )

        if adherence.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Adherence record already logged as {adherence.status}."
            )

        adherence.status = log_in.status
        adherence.logged_time = datetime.utcnow()
        adherence.logged_by = actor_id
        adherence.source = log_in.source
        
        self.uow.session.add(adherence)

        # Audit log entry
        audit = AuditLog(
            actor_id=actor_id,
            action="MEDICATION_ADHERENCE_LOG",
            entity_type="medication_adherence",
            entity_id=adherence.id,
            new_value={"detail": f"Logged medication schedule status as {log_in.status}"}
        )
        self.uow.session.add(audit)
        return adherence
