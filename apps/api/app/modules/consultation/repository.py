from sqlalchemy.future import select
from typing import List, Optional, Any
import sys
import os
import uuid

# Ensure backend-core is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages", "backend-core")))

from database.repository import BaseRepository
from database.models import Consultation

class ConsultationRepository(BaseRepository[Consultation, Any, Any]):
    def __init__(self, db):
        super().__init__(Consultation, db)

    async def get_by_appointment(self, appointment_id: uuid.UUID) -> Optional[Consultation]:
        query = select(Consultation).filter(
            Consultation.appointment_id == appointment_id,
            Consultation.deleted_at == None
        )
        result = await self.db.execute(query)
        return result.scalars().first()
