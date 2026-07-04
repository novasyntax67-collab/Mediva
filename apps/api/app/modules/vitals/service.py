from app.core.unit_of_work import APIUnitOfWork
from app.modules.vitals.schemas import VitalIngest
from database.models import Vital, MeasurementType, Device, AuditLog, Patient
from fastapi import HTTPException, status
from sqlalchemy.future import select
from datetime import datetime
from typing import List
import uuid
import sys
import os

# Ensure backend-core is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages", "backend-core")))

from events.events import vital_recorded

class VitalsService:
    def __init__(self, uow: APIUnitOfWork):
        self.uow = uow

    async def ingest_vital(
        self, patient_id: uuid.UUID, obj_in: VitalIngest, actor_id: uuid.UUID
    ) -> Vital:
        """
        Ingests vital signal observations, performs clinical range thresholding, 
        and links device sensors dynamically.
        """
        # 1. Fetch or dynamically register MeasurementType (dictionary entry)
        query_type = select(MeasurementType).filter(
            MeasurementType.code == obj_in.measurement_code,
            MeasurementType.deleted_at == None
        )
        res_type = await self.uow.session.execute(query_type)
        measurement_type = res_type.scalars().first()

        if not measurement_type:
            # Register a generic fallback measurement classification
            display_name = obj_in.measurement_code.replace("_", " ").title()
            measurement_type = MeasurementType(
                code=obj_in.measurement_code,
                display_name=display_name,
                unit="unit",
                is_active=True
            )
            self.uow.session.add(measurement_type)
            await self.uow.flush()

        # 2. Resolve Device serial links if provided
        device_id = None
        if obj_in.device_serial_number:
            query_device = select(Device).filter(
                Device.serial_number == obj_in.device_serial_number,
                Device.deleted_at == None
            )
            res_device = await self.uow.session.execute(query_device)
            device = res_device.scalars().first()

            if not device:
                # Fetch patient organization to map device ownership correctly
                patient = await self.uow.session.get(Patient, patient_id)
                org_id = patient.organization_id if patient else uuid.UUID("00000000-0000-0000-0000-000000000000")
                
                # Dynamically register device sensor
                device = Device(
                    serial_number=obj_in.device_serial_number,
                    manufacturer="Mock Sensor Manufacturer",
                    model="Wearable Node Gen-1",
                    device_type="Wearable",
                    organization_id=org_id
                )
                self.uow.session.add(device)
                await self.uow.flush()
                
            device_id = device.id

        # 3. Clinical thresholding check (flags anomalies)
        status_val = "normal"
        if obj_in.value_numeric is not None:
            low = measurement_type.normal_range_low
            high = measurement_type.normal_range_high

            if low is not None and obj_in.value_numeric < float(low):
                status_val = "abnormal"
            elif high is not None and obj_in.value_numeric > float(high):
                status_val = "abnormal"

        # 4. Insert Vital Observation
        vital = Vital(
            patient_id=patient_id,
            measurement_type_id=measurement_type.id,
            value_numeric=obj_in.value_numeric,
            value_text=obj_in.value_text,
            unit=measurement_type.unit,
            device_id=device_id,
            source=obj_in.source,
            status=status_val,
            validated=(obj_in.source == "manual"),
            recorded_at=obj_in.recorded_at
        )
        self.uow.session.add(vital)
        await self.uow.flush()

        # Log audit entry
        audit = AuditLog(
            actor_id=actor_id,
            action="VITAL_INGEST",
            entity_type="vitals",
            entity_id=vital.id,
            new_value={"detail": f"Ingested {obj_in.measurement_code} value={obj_in.value_numeric} status={status_val}"}
        )
        self.uow.session.add(audit)

        # Collect domain event — Risk Worker evaluates thresholds asynchronously
        self.uow.collect_event(
            vital_recorded(
                vital_id=str(vital.id),
                patient_id=str(patient_id),
                measurement_code=obj_in.measurement_code,
                value_numeric=obj_in.value_numeric,
                status_val=status_val,
                actor_id=str(actor_id),
            )
        )
        return vital

    async def get_vitals_timeline(
        self, patient_id: uuid.UUID, measurement_code: str, limit: int = 50
    ) -> List[Vital]:
        """Fetches chronological vitals timeline for a patient."""
        query = select(Vital).join(MeasurementType).filter(
            Vital.patient_id == patient_id,
            MeasurementType.code == measurement_code,
            Vital.deleted_at == None
        ).order_by(Vital.recorded_at.desc()).limit(limit)

        res = await self.uow.session.execute(query)
        return list(res.scalars().all())
