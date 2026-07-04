from sqlalchemy.future import select
from datetime import datetime
from typing import List, Optional, Any
import sys
import os
import uuid

# Ensure backend-core is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages", "backend-core")))

from database.repository import BaseRepository
from database.models import Vital

class VitalsRepository(BaseRepository[Vital, Any, Any]):
    def __init__(self, db):
        # We pass dummy schemas since Vitals are ingested dynamically
        super().__init__(Vital, db)

    async def get_patient_vitals_timeline(
        self, patient_id: uuid.UUID, measurement_type_id: Optional[uuid.UUID] = None, limit: int = 100
    ) -> List[Vital]:
        query = select(Vital).filter(
            Vital.patient_id == patient_id,
            Vital.deleted_at == None
        )
        if measurement_type_id:
            query = query.filter(Vital.measurement_type_id == measurement_type_id)
            
        # Leverage high-performance composite index: (patient_id, recorded_at DESC)
        query = query.order_by(Vital.recorded_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
