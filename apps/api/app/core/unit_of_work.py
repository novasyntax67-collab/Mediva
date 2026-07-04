from sqlalchemy.ext.asyncio import AsyncSession
import sys
import os

# Ensure backend-core is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages", "backend-core")))

from database.unit_of_work import UnitOfWork as BaseUnitOfWork
from app.modules.patients.repository import PatientRepository
from app.modules.vitals.repository import VitalsRepository
from app.modules.appointments.repository import AppointmentRepository
from app.modules.consultation.repository import ConsultationRepository

class APIUnitOfWork(BaseUnitOfWork):
    """
    Application-specific transaction coordinator binding domain repositories
    to a single database session context.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.patients = PatientRepository(session)
        self.vitals = VitalsRepository(session)
        self.appointments = AppointmentRepository(session)
        self.consultations = ConsultationRepository(session)
