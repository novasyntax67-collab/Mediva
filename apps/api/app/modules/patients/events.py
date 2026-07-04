import logging

logger = logging.getLogger(__name__)

async def emit_patient_registered_event(patient_id: str):
    logger.info(f"Event: Patient registered - ID: {patient_id}")
