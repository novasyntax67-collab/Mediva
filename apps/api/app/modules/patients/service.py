import asyncio
from app.core.unit_of_work import APIUnitOfWork
from app.modules.patients.schemas import PatientCreate, PatientUpdate
from fastapi import HTTPException, status
import uuid

class PatientService:
    def __init__(self, uow: APIUnitOfWork):
        self.uow = uow

    async def get_patient(self, patient_id: uuid.UUID):
        patient = await self.uow.patients.get(patient_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        return patient

    async def register_patient(self, obj_in: PatientCreate, actor_id: uuid.UUID):
        # Verify if profile already registered as patient
        existing = await self.uow.patients.get(obj_in.id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient already registered"
            )
        
        # Verify MRN uniqueness for the target organization
        mrn_check = await self.uow.patients.get_by_mrn(obj_in.organization_id, obj_in.mrn)
        if mrn_check:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Patient with MRN {obj_in.mrn} already exists in this organization"
            )

        return await self.uow.patients.create(obj_in=obj_in, actor_id=actor_id)

    async def update_patient(self, patient_id: uuid.UUID, obj_in: PatientUpdate, actor_id: uuid.UUID):
        patient = await self.get_patient(patient_id)
        return await self.uow.patients.update(db_obj=patient, obj_in=obj_in, actor_id=actor_id)

    async def search_patients(self, query_str: str, limit: int = 50):
        return await self.uow.patients.search_patients(query_str, limit)

    async def get_care_team(self, patient_id: uuid.UUID):
        # Verify patient exists
        await self.get_patient(patient_id)
        return await self.uow.patients.get_care_team(patient_id)

    async def get_patient_timeline(self, patient_id: uuid.UUID, limit: int = 50) -> list:
        # Verify patient exists
        await self.get_patient(patient_id)
        
        # Fetch vitals and appointments in parallel context
        vitals_task = self.uow.vitals.get_patient_vitals_timeline(patient_id, limit=limit)
        appointments_task = self.uow.appointments.get_patient_appointments(patient_id, limit=limit)
        
        vitals, appointments = await asyncio.gather(vitals_task, appointments_task)
        
        timeline = []
        for v in vitals:
            timeline.append({
                "type": "vital",
                "id": str(v.id),
                "recorded_at": v.recorded_at,
                "display": f"Vital logged: {v.value_numeric} {v.unit or ''} (confidence: {v.confidence})"
            })
        for a in appointments:
            timeline.append({
                "type": "appointment",
                "id": str(a.id),
                "recorded_at": a.scheduled_time,
                "display": f"Appointment scheduled with Doctor ID {a.doctor_id} - status: {a.status}"
            })
            
        timeline.sort(key=lambda x: x["recorded_at"], reverse=True)
        return timeline[:limit]
