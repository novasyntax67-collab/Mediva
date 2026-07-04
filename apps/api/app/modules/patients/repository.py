from sqlalchemy.future import select
from app.modules.patients.schemas import PatientCreate, PatientUpdate
import sys
import os
import uuid

# Ensure backend-core is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages", "backend-core")))

from database.repository import BaseRepository
from database.models import Patient, Profile, Doctor, CaregiverAssignment

class PatientRepository(BaseRepository[Patient, PatientCreate, PatientUpdate]):
    def __init__(self, db):
        super().__init__(Patient, db)

    async def get_by_mrn(self, organization_id: uuid.UUID, mrn: str) -> Patient | None:
        query = select(Patient).filter(
            Patient.organization_id == organization_id,
            Patient.mrn == mrn,
            Patient.deleted_at == None
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def search_patients(self, query_str: str, limit: int = 50) -> list:
        # Search by MRN, name, or email
        query = select(Patient).join(Profile, Patient.id == Profile.id).filter(
            (Patient.mrn.ilike(f"%{query_str}%") |
             Profile.first_name.ilike(f"%{query_str}%") |
             Profile.last_name.ilike(f"%{query_str}%") |
             Profile.email.ilike(f"%{query_str}%")),
            Patient.deleted_at == None
        ).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_care_team(self, patient_id: uuid.UUID) -> dict:
        # Fetch primary doctor
        query_doc = select(Profile).join(Doctor, Profile.id == Doctor.id).filter(
            Doctor.id == select(Patient.primary_doctor_id).filter(Patient.id == patient_id).scalar_subquery(),
            Doctor.deleted_at == None
        )
        # Fetch caregivers
        query_cg = select(Profile).join(CaregiverAssignment, Profile.id == CaregiverAssignment.caregiver_id).filter(
            CaregiverAssignment.patient_id == patient_id,
            CaregiverAssignment.approved_by_patient == True,
            CaregiverAssignment.deleted_at == None
        )
        
        result_doc = await self.db.execute(query_doc)
        result_cg = await self.db.execute(query_cg)
        
        return {
            "primary_doctor": result_doc.scalars().first(),
            "caregivers": result_cg.scalars().all()
        }
