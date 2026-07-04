from sqlalchemy.future import select
from datetime import datetime
from typing import List, Optional, Any
import sys
import os
import uuid

# Ensure backend-core is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages", "backend-core")))

from database.repository import BaseRepository
from database.models import Appointment

class AppointmentRepository(BaseRepository[Appointment, Any, Any]):
    def __init__(self, db):
        super().__init__(Appointment, db)

    async def get_doctor_schedule(
        self, doctor_id: uuid.UUID, start_time: datetime, end_time: datetime
    ) -> List[Appointment]:
        query = select(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.scheduled_time >= start_time,
            Appointment.scheduled_time <= end_time,
            Appointment.deleted_at == None
        )
        
        # Leverage high-performance composite index: (doctor_id, scheduled_time)
        query = query.order_by(Appointment.scheduled_time.asc())
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_patient_appointments(
        self, patient_id: uuid.UUID, limit: int = 50
    ) -> List[Appointment]:
        query = select(Appointment).filter(
            Appointment.patient_id == patient_id,
            Appointment.deleted_at == None
        ).order_by(Appointment.scheduled_time.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
