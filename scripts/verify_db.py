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

async def verify():
    if not DATABASE_URL:
        print("Error: DATABASE_URL not found in environment!")
        return

    print("Connecting to Supabase Database...")
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # 1. Alembic Version Table Check
        print("\n--- Checking Alembic Version ---")
        try:
            version = await conn.fetchval("SELECT version_num FROM alembic_version;")
            print(f"Active alembic revision: {version}")
        except Exception as e:
            print(f"Error fetching alembic version: {e}")

        # 2. Table Count Check
        print("\n--- Counting Tables in public schema ---")
        count = await conn.fetchval(
            "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"
        )
        print(f"Total tables found: {count}")

        # 3. List Core Tables
        print("\n--- Verifying Core Tables ---")
        tables = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"
        )
        for t in tables:
            print(f" - {t['tablename']}")

        # 4. Foreign Key Count
        print("\n--- Verifying Foreign Keys ---")
        fkeys = await conn.fetch("""
            SELECT count(*) 
            FROM information_schema.table_constraints tc
            WHERE tc.constraint_type='FOREIGN KEY';
        """)
        print(f"Total active Foreign Key constraints: {fkeys[0][0]}")

        # 5. Row-Level Security State
        print("\n--- Row Level Security (RLS) Status ---")
        rls_status = await conn.fetch("""
            SELECT tablename, rowsecurity
            FROM pg_tables
            WHERE schemaname='public'
            ORDER BY tablename;
        """)
        for r in rls_status:
            print(f" - Table '{r['tablename']}': RLS Enabled = {r['rowsecurity']}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(verify())
