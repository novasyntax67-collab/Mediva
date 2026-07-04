from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

class VitalIngest(BaseModel):
    measurement_code: str
    value_numeric: Optional[float] = None
    value_text: Optional[str] = None
    device_serial_number: Optional[str] = None
    recorded_at: datetime
    source: str = "manual" # manual, device, wearable

class VitalInDB(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    measurement_type_id: uuid.UUID
    value_numeric: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    device_id: Optional[uuid.UUID] = None
    source: str
    confidence: float
    status: str
    validated: bool
    recorded_at: datetime

    class Config:
        from_attributes = True

class DeviceRegister(BaseModel):
    serial_number: str
    manufacturer: str
    model: str
    device_type: Optional[str] = None
    connection_type: Optional[str] = None
