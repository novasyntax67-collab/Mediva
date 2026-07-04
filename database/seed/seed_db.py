import asyncio
import os
import sys
from datetime import date, datetime, timedelta
import uuid
from dotenv import load_dotenv

# Ensure backend-core is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "packages", "backend-core")))

# Load environmental configs
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "api", ".env"))

from database.session import async_session_maker
from database.models import (
    Role, Permission, RolePermission, MeasurementType, 
    Organization, Clinic, Profile, ProfileRole, Doctor, 
    Patient, CaregiverAssignment, Consent, ConsentGrant, Device, SystemSetting
)

async def seed_database():
    print("Starting database seeding...")
    async with async_session_maker() as session:
        try:
            # 1. Seed Roles
            print("Seeding Roles...")
            roles_data = [
                {"name": "super_admin", "description": "Global administrator with root privileges"},
                {"name": "org_admin", "description": "Organization-level administrator"},
                {"name": "doctor", "description": "Clinician / Medical provider role"},
                {"name": "patient", "description": "Healthcare patient role"},
                {"name": "caregiver", "description": "Patient family member or caregiver role"},
            ]
            roles_map = {}
            for rd in roles_data:
                role = Role(name=rd["name"], description=rd["description"])
                session.add(role)
                roles_map[rd["name"]] = role
            await session.flush()

            # 2. Seed Permissions
            print("Seeding Permissions...")
            perms_data = [
                {"name": "vitals:read", "description": "Read access to vital signs"},
                {"name": "vitals:write", "description": "Log new vital readings"},
                {"name": "records:read", "description": "View medical history and charts"},
                {"name": "records:write", "description": "Modify patient medical history"},
                {"name": "prescriptions:write", "description": "Write and authorize prescriptions"},
                {"name": "orgs:manage", "description": "Manage organizations and clinics"},
            ]
            perms_map = {}
            for pd in perms_data:
                perm = Permission(name=pd["name"], description=pd["description"])
                session.add(perm)
                perms_map[pd["name"]] = perm
            await session.flush()

            # 3. Seed Role-Permissions
            print("Seeding Role-Permissions Map...")
            role_perms = [
                # Super Admin gets all
                ("super_admin", "vitals:read"), ("super_admin", "vitals:write"),
                ("super_admin", "records:read"), ("super_admin", "records:write"),
                ("super_admin", "prescriptions:write"), ("super_admin", "orgs:manage"),
                # Org Admin
                ("org_admin", "vitals:read"), ("org_admin", "records:read"), ("org_admin", "orgs:manage"),
                # Doctor
                ("doctor", "vitals:read"), ("doctor", "vitals:write"),
                ("doctor", "records:read"), ("doctor", "records:write"),
                ("doctor", "prescriptions:write"),
                # Patient
                ("patient", "vitals:read"), ("patient", "vitals:write"), ("patient", "records:read"),
                # Caregiver
                ("caregiver", "vitals:read"), ("caregiver", "records:read"),
            ]
            for r_name, p_name in role_perms:
                rp = RolePermission(role_id=roles_map[r_name].id, permission_id=perms_map[p_name].id)
                session.add(rp)

            # 4. Seed Measurement Types (Vitals metadata)
            print("Seeding Measurement Types (UCUM/LOINC)...")
            measurements = [
                {
                    "code": "LOINC_8867-4",
                    "display_name": "Heart Rate",
                    "category": "cardiology",
                    "unit": "bpm",
                    "normal_range_low": 60.0,
                    "normal_range_high": 100.0,
                    "decimal_precision": 0,
                    "is_numeric": True,
                },
                {
                    "code": "LOINC_8480-6",
                    "display_name": "Systolic Blood Pressure",
                    "category": "cardiology",
                    "unit": "mm[Hg]",
                    "normal_range_low": 90.0,
                    "normal_range_high": 120.0,
                    "decimal_precision": 0,
                    "is_numeric": True,
                },
                {
                    "code": "LOINC_8462-4",
                    "display_name": "Diastolic Blood Pressure",
                    "category": "cardiology",
                    "unit": "mm[Hg]",
                    "normal_range_low": 60.0,
                    "normal_range_high": 80.0,
                    "decimal_precision": 0,
                    "is_numeric": True,
                },
                {
                    "code": "LOINC_59408-5",
                    "display_name": "Oxygen Saturation",
                    "category": "pulmonology",
                    "unit": "%",
                    "normal_range_low": 95.0,
                    "normal_range_high": 100.0,
                    "decimal_precision": 1,
                    "is_numeric": True,
                },
                {
                    "code": "LOINC_8310-5",
                    "display_name": "Body Temperature",
                    "category": "general",
                    "unit": "Cel",
                    "normal_range_low": 36.1,
                    "normal_range_high": 37.2,
                    "decimal_precision": 1,
                    "is_numeric": True,
                },
            ]
            for m in measurements:
                mt = MeasurementType(**m)
                session.add(mt)

            # 5. Seed Organizations
            print("Seeding Organizations...")
            org = Organization(name="Mediva Health System", status="active")
            session.add(org)
            await session.flush()

            # 6. Seed Clinics
            print("Seeding Clinics...")
            clinic = Clinic(
                organization_id=org.id,
                name="Mediva Telehealth Hub",
                address="100 Medical Plaza, Suite 400",
                timezone="Australia/Sydney",
                phone="+61 2 9876 5432",
                status="active"
            )
            session.add(clinic)
            await session.flush()

            # 7. Seed System Settings
            setting = SystemSetting(
                organization_id=org.id,
                timezone="Australia/Sydney",
                language="en",
                measurement_system="metric",
                ai_features_enabled=True,
                telehealth_provider="livekit"
            )
            session.add(setting)

            # 8. Seed Demo Profiles (Doctor, Patient, Caregiver)
            print("Seeding Profiles...")
            # Demo Doctor Profile
            doc_profile = Profile(
                email="jane.doe@medivahealth.com",
                first_name="Jane",
                last_name="Doe",
                phone="+61 400 123 456"
            )
            session.add(doc_profile)
            
            # Demo Patient Profile
            pat_profile = Profile(
                email="john.smith@medivapatient.com",
                first_name="John",
                last_name="Smith",
                phone="+61 400 987 654"
            )
            session.add(pat_profile)

            # Demo Caregiver Profile
            cg_profile = Profile(
                email="sarah.smith@medivacaregiver.com",
                first_name="Sarah",
                last_name="Smith",
                phone="+61 400 555 123"
            )
            session.add(cg_profile)
            await session.flush()

            # Map Profile Roles
            session.add(ProfileRole(profile_id=doc_profile.id, role_id=roles_map["doctor"].id))
            session.add(ProfileRole(profile_id=pat_profile.id, role_id=roles_map["patient"].id))
            session.add(ProfileRole(profile_id=cg_profile.id, role_id=roles_map["caregiver"].id))

            # 9. Seed Doctor & Patient Entity Details
            print("Seeding Doctor & Patient clinical data...")
            doctor = Doctor(
                id=doc_profile.id,
                specialty="Cardiologist",
                license_number="MED1000987",
                organization_id=org.id,
                consultation_fee=150.00,
                timezone="Australia/Sydney",
                experience_years=12,
                license_expiry=date(2028, 12, 31),
                accepting_patients=True
            )
            session.add(doctor)
            await session.flush()

            patient = Patient(
                id=pat_profile.id,
                mrn="MRN-8871-A",
                organization_id=org.id,
                primary_doctor_id=doctor.id,
                status="active",
                date_of_birth=date(1985, 5, 20),
                gender="male",
                blood_group="O+",
                height=180.5,
                weight=82.3,
                preferred_language="en"
            )
            session.add(patient)
            await session.flush()

            # 10. Seed Caregiver Assignment
            print("Seeding Caregiver Assignment...")
            assignment = CaregiverAssignment(
                patient_id=patient.id,
                caregiver_id=cg_profile.id,
                relationship="spouse",
                approved_by_patient=True
            )
            session.add(assignment)

            # 11. Seed Consents & Consent Grants
            print("Seeding Consents & Grants...")
            consent = Consent(
                name="telehealth_agreement",
                text="Consent to receive treatment and consultation via telehealth audio-visual services."
            )
            session.add(consent)
            await session.flush()

            grant = ConsentGrant(
                patient_id=patient.id,
                consent_id=consent.id,
                granted_to=cg_profile.id,
                purpose="care_management",
                granted_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=365)
            )
            session.add(grant)

            # 12. Seed Devices
            print("Seeding IoT Devices...")
            device = Device(
                serial_number="SN-HR-C2026-X1",
                manufacturer="MedivaIoT Labs",
                model="HeartLink V2",
                firmware="v1.4.2",
                connection_type="cellular",
                battery=94,
                device_type="wearable",
                sdk="mediva-pulse-sdk",
                supported_measurements={"heart_rate": True, "spo2": True},
                organization_id=org.id
            )
            session.add(device)

            await session.commit()
            print("\nDatabase seeding completed successfully!")

        except Exception as e:
            await session.rollback()
            print(f"\nError seeding database: {e}")

if __name__ == "__main__":
    asyncio.run(seed_database())
