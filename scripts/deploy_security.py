import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load env configurations
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "apps", "api", ".env"))
DATABASE_URL = os.getenv("DATABASE_URL")

# Resolve pg scheme to raw postgresql for asyncpg
if DATABASE_URL and DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)

# Sequence of helper SQL functions
FUNCTIONS = [
    "001_roles.sql",
    "002_membership.sql",
    "003_patient.sql",
    "004_break_glass.sql",
]

# Sequence of RLS policies
POLICIES = [
    "001_profiles.sql",
    "002_organizations.sql",
    "003_patients.sql",
    "004_appointments.sql",
    "005_consultations.sql",
    "006_vitals.sql",
    "007_prescriptions.sql",
    "008_reports.sql",
    "009_notifications.sql",
    "010_audit.sql",
    "011_break_glass.sql",
]

async def deploy():
    if not DATABASE_URL:
        print("Error: DATABASE_URL not found in env!")
        return

    print("Connecting to Database...")
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Deploy helper functions
        print("\n=== Deploying SQL Helper Functions ===")
        for func in FUNCTIONS:
            filepath = os.path.join(os.path.dirname(__file__), "..", "database", "functions", func)
            print(f"Deploying function script: {func}...")
            with open(filepath, "r", encoding="utf-8") as f:
                sql = f.read()
                await conn.execute(sql)

        # Deploy RLS policies
        print("\n=== Deploying Row-Level Security Policies ===")
        for policy in POLICIES:
            filepath = os.path.join(os.path.dirname(__file__), "..", "database", "policies", policy)
            print(f"Deploying policy script: {policy}...")
            with open(filepath, "r", encoding="utf-8") as f:
                sql = f.read()
                await conn.execute(sql)

        print("\nDeployment completed successfully!")

    except Exception as e:
        print(f"\nError during deployment: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(deploy())
