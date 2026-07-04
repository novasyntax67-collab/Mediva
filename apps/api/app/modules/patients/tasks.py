import logging

logger = logging.getLogger(__name__)

def process_patient_onboarding(patient_id: str):
    logger.info(f"Background Task: Processing onboarding for Patient ID: {patient_id}")
