from sqlalchemy import (
    Column,
    DateTime,
    String,
    Integer,
    Boolean,
    ForeignKey,
    Numeric,
    Text,
    Date,
    Index,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()

# ==============================================================================
# BASE ABSTRACT MODELS
# ==============================================================================

class BaseModel(Base):
    __abstract__ = True
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

class AuditModel(BaseModel):
    __abstract__ = True
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

class LockableModel(AuditModel):
    __abstract__ = True
    lock_version = Column(Integer, default=1, nullable=False)

class VersionedModel(LockableModel):
    __abstract__ = True
    version = Column(Integer, default=1, nullable=False)
    is_current = Column(Boolean, default=True, nullable=False)
    # superseded_by column is added dynamically on tables that inherit this class

# ==============================================================================
# ACCESS CONTROL & ORGS
# ==============================================================================

class Profile(BaseModel):
    __tablename__ = "profiles"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=True)
    photo_url = Column(String(500), nullable=True)
    
    # Relationships
    roles = relationship("ProfileRole", back_populates="profile")
    organizations = relationship("OrganizationMember", back_populates="profile")

class Role(BaseModel):
    __tablename__ = "roles"
    
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    permissions = relationship("RolePermission", back_populates="role")

class Permission(BaseModel):
    __tablename__ = "permissions"
    
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

class RolePermission(BaseModel):
    __tablename__ = "role_permissions"
    
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission")

class ProfileRole(BaseModel):
    __tablename__ = "profile_roles"
    
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    profile = relationship("Profile", back_populates="roles")
    role = relationship("Role")

class Organization(BaseModel):
    __tablename__ = "organizations"
    
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="active", nullable=False)
    parent_organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    
    # Relationships
    clinics = relationship("Clinic", back_populates="organization")
    members = relationship("OrganizationMember", back_populates="organization")

class Clinic(LockableModel):
    __tablename__ = "clinics"
    
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    timezone = Column(String(100), default="UTC", nullable=False)
    phone = Column(String(50), nullable=True)
    status = Column(String(50), default="active", nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="clinics")

class OrganizationMember(BaseModel):
    __tablename__ = "organization_members"
    
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="active", nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="members")
    profile = relationship("Profile", back_populates="organizations")

# ==============================================================================
# PATIENTS & CLINICIANS
# ==============================================================================

class Doctor(DoctorProfile := LockableModel):
    __tablename__ = "doctors"
    
    id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True)
    specialty = Column(String(150), nullable=True)
    license_number = Column(String(100), unique=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    consultation_fee = Column(Numeric(8, 2), nullable=True)
    timezone = Column(String(100), default="UTC", nullable=False)
    availability_template = Column(JSONB, nullable=True)
    experience_years = Column(Integer, nullable=True)
    license_expiry = Column(Date, nullable=True)
    accepting_patients = Column(Boolean, default=True, nullable=False)

class Patient(LockableModel):
    __tablename__ = "patients"
    
    id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True)
    mrn = Column(String(100), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    primary_doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=True)
    status = Column(String(50), default="active", nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(50), nullable=True)
    blood_group = Column(String(20), nullable=True)
    height = Column(Numeric(5, 2), nullable=True) # cm
    weight = Column(Numeric(5, 2), nullable=True) # kg
    preferred_language = Column(String(50), default="en", nullable=False)
    photo_url = Column(String(500), nullable=True)
    deceased_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        UniqueConstraint("organization_id", "mrn", name="uq_org_patient_mrn"),
    )

class PatientContact(BaseModel):
    __tablename__ = "patient_contacts"
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    relationship = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=False)
    email = Column(String(255), nullable=True)
    priority = Column(Integer, default=1, nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)

class CaregiverAssignment(BaseModel):
    __tablename__ = "caregiver_assignments"
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    caregiver_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    relationship = Column(String(100), nullable=True)
    permissions = Column(JSONB, nullable=True)
    approved_by_patient = Column(Boolean, default=False, nullable=False)

# ==============================================================================
# VITALS & DEVICES
# ==============================================================================

class MeasurementType(LockableModel):
    __tablename__ = "measurement_types"
    
    code = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=True)
    unit = Column(String(50), nullable=True)
    normal_range_low = Column(Numeric(10, 3), nullable=True)
    normal_range_high = Column(Numeric(10, 3), nullable=True)
    decimal_precision = Column(Integer, server_default="2", default=2, nullable=False)
    is_numeric = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

class Vital(BaseModel):
    __tablename__ = "vitals"
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    measurement_type_id = Column(UUID(as_uuid=True), ForeignKey("measurement_types.id"), nullable=False)
    value_numeric = Column(Numeric(10, 3), nullable=True)
    value_text = Column(String(255), nullable=True)
    value_json = Column(JSONB, nullable=True)
    unit = Column(String(50), nullable=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)
    source = Column(String(100), default="manual", nullable=False)
    confidence = Column(Numeric(5, 2), default=1.00, nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    validated = Column(Boolean, default=False, nullable=False)
    validation_source = Column(String(255), nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False)

class Device(BaseModel):
    __tablename__ = "devices"
    
    serial_number = Column(String(100), unique=True, nullable=False, index=True)
    manufacturer = Column(String(150), nullable=False)
    model = Column(String(150), nullable=False)
    firmware = Column(String(100), nullable=True)
    connection_type = Column(String(100), nullable=True)
    battery = Column(Integer, nullable=True)
    device_type = Column(String(100), nullable=True)
    sdk = Column(String(100), nullable=True)
    supported_measurements = Column(JSONB, nullable=True)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

class DeviceAssignment(BaseModel):
    __tablename__ = "device_assignments"
    
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    unassigned_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="active", nullable=False)

# ==============================================================================
# TELEHEALTH & ENCOUNTERS
# ==============================================================================

class Appointment(LockableModel):
    __tablename__ = "appointments"
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False)
    clinic_id = Column(UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False)
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    duration = Column(Integer, default=30, nullable=False) # minutes
    visit_type = Column(String(50), default="telehealth", nullable=False)
    location = Column(String(255), nullable=True)
    reason = Column(Text, nullable=True)
    priority = Column(String(50), default="routine", nullable=False)
    status = Column(String(50), default="scheduled", nullable=False)
    cancel_reason = Column(Text, nullable=True)
    booked_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    checked_in_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    rescheduled_from = Column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=True)
    meeting_provider = Column(String(100), nullable=True)
    meeting_url = Column(String(500), nullable=True)

class AppointmentParticipant(BaseModel):
    __tablename__ = "appointment_participants"
    
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(100), default="patient", nullable=False)
    required = Column(Boolean, default=True, nullable=False)
    status = Column(String(50), default="accepted", nullable=False)

class Consultation(Base):
    __tablename__ = "consultations"
    
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="CASCADE"), primary_key=True)
    room_id = Column(String(150), nullable=True)
    chief_complaint = Column(Text, nullable=True)
    soap_notes = Column(JSONB, nullable=True)
    summary = Column(Text, nullable=True)
    follow_up = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="completed", nullable=False)
    
    # Standard auditing, locking and soft-delete columns manually defined to prevent composite PK
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    lock_version = Column(Integer, default=1, nullable=False)

class ConsultationDiagnosis(BaseModel):
    __tablename__ = "consultation_diagnoses"
    
    consultation_id = Column(UUID(as_uuid=True), ForeignKey("consultations.appointment_id", ondelete="CASCADE"), nullable=False)
    condition_id = Column(UUID(as_uuid=True), ForeignKey("conditions.id"), nullable=False)
    is_primary = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)

# ==============================================================================
# CLINICAL HISTORY, DOCUMENTS & PLANS
# ==============================================================================

class Condition(BaseModel):
    __tablename__ = "conditions"
    
    code_system = Column(String(100), default="ICD-10", nullable=False)
    code = Column(String(100), nullable=False)
    display = Column(String(255), nullable=False)
    version = Column(String(50), nullable=True)
    
    __table_args__ = (
        UniqueConstraint("code_system", "code", name="uq_condition_code"),
    )

class PatientCondition(BaseModel):
    __tablename__ = "patient_conditions"
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    condition_id = Column(UUID(as_uuid=True), ForeignKey("conditions.id"), nullable=False)
    onset_date = Column(Date, nullable=True)
    status = Column(String(50), default="active", nullable=False)

class Allergy(BaseModel):
    __tablename__ = "allergies"
    
    code_system = Column(String(100), default="SNOMED", nullable=False)
    code = Column(String(100), nullable=False)
    display = Column(String(255), nullable=False)
    version = Column(String(50), nullable=True)
    
    __table_args__ = (
        UniqueConstraint("code_system", "code", name="uq_allergy_code"),
    )

class PatientAllergy(BaseModel):
    __tablename__ = "patient_allergies"
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    allergy_id = Column(UUID(as_uuid=True), ForeignKey("allergies.id"), nullable=False)
    severity = Column(String(50), nullable=True)
    reaction = Column(String(255), nullable=True)
    status = Column(String(50), default="active", nullable=False)

class FamilyHistory(BaseModel):
    __tablename__ = "family_history"
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    relative_relationship = Column(String(100), nullable=False)
    condition_code = Column(String(100), nullable=False)
    onset_age = Column(Integer, nullable=True)
    status = Column(String(50), default="active", nullable=False)

class CarePlan(VersionedModel):
    __tablename__ = "care_plans"
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="active", nullable=False)
    superseded_by = Column(UUID(as_uuid=True), ForeignKey("care_plans.id"), nullable=True)

class CarePlanTask(BaseModel):
    __tablename__ = "care_plan_tasks"
    
    care_plan_id = Column(UUID(as_uuid=True), ForeignKey("care_plans.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending", nullable=False)

class LabOrder(BaseModel):
    __tablename__ = "lab_orders"
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False)
    order_date = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    status = Column(String(50), default="ordered", nullable=False)

class LabResult(BaseModel):
    __tablename__ = "lab_results"
    
    lab_order_id = Column(UUID(as_uuid=True), ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False)
    test_name = Column(String(200), nullable=False)
    value_numeric = Column(Numeric(10, 3), nullable=True)
    value_text = Column(String(255), nullable=True)
    unit = Column(String(50), nullable=True)
    reference_range = Column(String(100), nullable=True)
    status = Column(String(50), default="final", nullable=False)

class LabReport(VersionedModel):
    __tablename__ = "lab_reports"
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    clinician_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False)
    report_date = Column(Date, nullable=False)
    ocr_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    superseded_by = Column(UUID(as_uuid=True), ForeignKey("lab_reports.id"), nullable=True)

class RadiologyReport(VersionedModel):
    __tablename__ = "radiology_reports"
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    clinician_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False)
    modality = Column(String(100), nullable=False)
    body_site = Column(String(150), nullable=False)
    findings = Column(Text, nullable=True)
    impression = Column(Text, nullable=True)
    superseded_by = Column(UUID(as_uuid=True), ForeignKey("radiology_reports.id"), nullable=True)

class MedicalDocument(BaseModel):
    __tablename__ = "medical_documents"
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    document_type = Column(String(100), nullable=False)

# ==============================================================================
# MEDICATIONS & PRESCRIPTIONS
# ==============================================================================

class Medication(BaseModel):
    __tablename__ = "medications"
    
    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=True) # RxNorm
    description = Column(Text, nullable=True)

class Prescription(VersionedModel):
    __tablename__ = "prescriptions"
    
    consultation_id = Column(UUID(as_uuid=True), ForeignKey("consultations.appointment_id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False)
    status = Column(String(50), default="active", nullable=False)
    superseded_by = Column(UUID(as_uuid=True), ForeignKey("prescriptions.id"), nullable=True)

class PrescriptionItem(BaseModel):
    __tablename__ = "prescription_items"
    
    prescription_id = Column(UUID(as_uuid=True), ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False)
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"), nullable=False)
    dosage_quantity = Column(Numeric(8, 3), nullable=False)
    dosage_unit = Column(String(50), nullable=False)
    frequency_interval = Column(Integer, nullable=False)
    frequency_period = Column(String(50), nullable=False) # e.g. hour, day
    duration_days = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    refills = Column(Integer, default=0, nullable=False)
    instructions = Column(Text, nullable=True)
    schedule_json = Column(JSONB, nullable=True)

class MedicationAdherence(BaseModel):
    __tablename__ = "medication_adherence"
    
    prescription_item_id = Column(UUID(as_uuid=True), ForeignKey("prescription_items.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    logged_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="pending", nullable=False)
    logged_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    source = Column(String(100), default="patient", nullable=False) # patient, caregiver, wearable
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)

# ==============================================================================
# AI ANALYTICS & TRIAGE
# ==============================================================================

class TriageSession(BaseModel):
    __tablename__ = "triage_sessions"
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    urgency = Column(String(50), nullable=True)
    recommended_action = Column(Text, nullable=True)
    escalated = Column(Boolean, default=False, nullable=False)
    escalated_to = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    guideline_reference = Column(Text, nullable=True)

class SymptomAssessment(BaseModel):
    __tablename__ = "symptom_assessments"
    
    triage_session_id = Column(UUID(as_uuid=True), ForeignKey("triage_sessions.id", ondelete="CASCADE"), nullable=False)
    symptom = Column(String(200), nullable=False)
    duration = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

class AIPrediction(BaseModel):
    __tablename__ = "ai_predictions"
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(100), nullable=False)
    score = Column(Numeric(5, 2), nullable=False)
    feature_importance = Column(JSONB, nullable=True)
    action_taken = Column(String(200), nullable=True)
    model_version = Column(String(50), nullable=False)
    prompt_version = Column(String(50), nullable=True)
    confidence_reason = Column(Text, nullable=True)
    reviewed_by_clinician = Column(Boolean, default=False, nullable=False)
    provider = Column(String(100), nullable=True)
    model_name = Column(String(100), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    token_usage = Column(JSONB, nullable=True)
    cost = Column(Numeric(10, 6), nullable=True)

class HealthScore(BaseModel):
    __tablename__ = "health_scores"
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    overall_score = Column(Numeric(5, 2), nullable=False)
    mobility_score = Column(Numeric(5, 2), nullable=True)
    cardiac_score = Column(Numeric(5, 2), nullable=True)
    trend = Column(String(50), nullable=True)

class RiskScore(BaseModel):
    __tablename__ = "risk_scores"
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(100), nullable=False)
    score = Column(Numeric(5, 2), nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

# ==============================================================================
# AUDITING, CONSENTS & SYSTEM CONFIG
# ==============================================================================

class Consent(BaseModel):
    __tablename__ = "consents"
    
    name = Column(String(150), unique=True, nullable=False, index=True)
    text = Column(Text, nullable=False)

class ConsentGrant(BaseModel):
    __tablename__ = "consent_grants"
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    consent_id = Column(UUID(as_uuid=True), ForeignKey("consents.id", ondelete="CASCADE"), nullable=False)
    granted_to = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    purpose = Column(String(200), nullable=True)
    granted_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    withdrawal_reason = Column(Text, nullable=True)

class AuditLog(BaseModel):
    __tablename__ = "audit_logs"
    
    actor_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(50), nullable=False)
    old_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(100), nullable=True)
    session_id = Column(String(100), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

class BreakGlassEvent(BaseModel):
    __tablename__ = "break_glass_events"
    
    actor_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    reason = Column(String(255), nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(50), nullable=True)
    device = Column(String(255), nullable=True)
    justification = Column(Text, nullable=False)

class Notification(BaseModel):
    __tablename__ = "notifications"
    
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)

class NotificationDelivery(BaseModel):
    __tablename__ = "notification_deliveries"
    
    notification_id = Column(UUID(as_uuid=True), ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String(50), nullable=False) # email, sms, push
    status = Column(String(50), default="pending", nullable=False) # pending, sent, failed
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    provider_message_id = Column(String(255), nullable=True)
    provider_response = Column(JSONB, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)

class Attachment(BaseModel):
    __tablename__ = "attachments"
    
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    storage_path = Column(String(500), nullable=False)
    bucket = Column(String(100), default="medical-documents", nullable=False)
    checksum = Column(String(100), nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    virus_scan_status = Column(String(50), default="pending", nullable=False)
    encrypted = Column(Boolean, default=True, nullable=False)
    retention_until = Column(DateTime(timezone=True), nullable=True)
    associated_type = Column(String(100), nullable=False)
    associated_id = Column(UUID(as_uuid=True), nullable=False)

class SystemSetting(BaseModel):
    __tablename__ = "system_settings"
    
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, nullable=True)
    timezone = Column(String(100), default="UTC", nullable=False)
    language = Column(String(50), default="en", nullable=False)
    measurement_system = Column(String(50), default="metric", nullable=False)
    notification_defaults = Column(JSONB, nullable=True)
    ai_features_enabled = Column(Boolean, default=True, nullable=False)
    telehealth_provider = Column(String(100), default="livekit", nullable=False)
    branding = Column(JSONB, nullable=True)

# ==============================================================================
# TRANSACTIONAL OUTBOX & EVENT PROCESSING
# ==============================================================================

class EventOutbox(BaseModel):
    """
    Transactional Outbox — events are written into this table inside the same
    database transaction as clinical records. A background Outbox Publisher
    polls pending rows and dispatches them to the EventBus (Celery/Redis).
    If the transaction rolls back, no event row exists. If it commits, the
    event is guaranteed to exist and will be delivered at-least-once.
    """
    __tablename__ = "event_outbox"

    event_type = Column(String(100), nullable=False, index=True)
    event_version = Column(Integer, default=1, nullable=False)
    aggregate_type = Column(String(100), nullable=False)
    aggregate_id = Column(UUID(as_uuid=True), nullable=False)
    payload = Column(JSONB, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    actor_id = Column(UUID(as_uuid=True), nullable=False)
    correlation_id = Column(UUID(as_uuid=True), nullable=True)
    causation_id = Column(UUID(as_uuid=True), nullable=True)

    # Publishing lifecycle
    status = Column(String(20), default="pending", nullable=False)  # pending | published | failed
    published_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=5, nullable=False)
    last_error = Column(Text, nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)


class ProcessedEvent(Base):
    """
    Idempotency guard — each worker records which events it has already
    processed. Composite PK (event_id, worker) allows independent tracking
    per consumer. Before acting on an event, the worker checks this table
    and skips duplicates.
    """
    __tablename__ = "processed_events"

    event_id = Column(UUID(as_uuid=True), primary_key=True)
    worker = Column(String(100), primary_key=True)
    processed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

# ==============================================================================
# INDEXING & CONSTRAINTS DEFINITIONS
# ==============================================================================
# Standard partial indexing on non-deleted records
Index("idx_profiles_deleted_at", Profile.deleted_at, postgresql_where=(Profile.deleted_at == None))
Index("idx_patients_deleted_at", Patient.deleted_at, postgresql_where=(Patient.deleted_at == None))
Index("idx_patients_org_id", Patient.organization_id, Patient.deleted_at)

# Composite Indexes for High-Performance Workloads
Index("idx_vitals_patient_timeline", Vital.patient_id, Vital.recorded_at.desc(), Vital.deleted_at)
Index("idx_appointments_doctor_schedule", Appointment.doctor_id, Appointment.scheduled_time, Appointment.deleted_at)
Index("idx_prescriptions_patient_status", Prescription.patient_id, Prescription.status, Prescription.deleted_at)
Index("idx_notifications_recipient_timeline", Notification.recipient_id, Notification.created_at.desc(), Notification.deleted_at)

# Outbox polling index — the publisher queries (status, created_at) with FOR UPDATE SKIP LOCKED
Index("idx_outbox_pending_poll", EventOutbox.status, EventOutbox.created_at, postgresql_where=(EventOutbox.status == "pending"))
Index("idx_outbox_failed", EventOutbox.status, postgresql_where=(EventOutbox.status == "failed"))

