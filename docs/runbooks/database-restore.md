# Database Restore Runbook

This guide details restoring the Supabase PostgreSQL database.

## Step 1: Obtain the Backup File
Download the backup dump `.sql` file from secure object storage bucket.

## Step 2: Stop Services
```bash
docker-compose down
```

## Step 3: Run Database Restoration
```bash
docker-compose up -d postgres
cat backup.sql | docker exec -i healthcare-postgres psql -U postgres -d healthcare
```
