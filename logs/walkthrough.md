# Carex v3 (10/10) Architecture Restructuring Walkthrough

This document records the final structural optimizations and architecture setups completed for the Carex Platform.

## Core Adjustments Made

### 1. Consolidated Deployables (`apps/`)
- **[ai-service](../apps/ai-service/)**: Consolidated all AI logic (`gateway`, `triage`, `anomaly`, `report`, `embeddings`, `medication`, `rag`, `shared`) into a single FastAPI deployable unit.
- **[worker](../apps/worker/)**: Consolidated all queue tasks (`notification`, `analytics`, `reminder`, `vitals`, `cleanup`, `emails`) into a single Celery worker with integrated Beat scheduling.
- **[api](../apps/api/)**: Clean core API configuration and versioned routing.
- **[web](../apps/web/)**: Next.js client with role-based routing layout groups (`(patient)`, `(clinician)`, etc.).

### 2. Consolidated Packages (`packages/`)
- **[backend-core](../packages/backend-core/)**: Shared python auth, database, configuration, telemetry, security, and exception decorators.
- **[healthcare](../packages/healthcare/)**: Tightly coupled healthcare operations (FHIR, HL7, Terminology schemas).
- **[sdk](../packages/sdk/)**: Automation targets (Typescript) for client SDK wrappers.

### 3. Database Isolation
- Replaced internal migrations with a standalone root **[database/](../database/)** containing separate subdirectories for policies, views, triggers, functions, seeds, and alembic configs.

### 4. Infrastructure & Telemetry
- Restructured `infrastructure/docker/` into base stages (`base/node`, `base/python`, `base/gpu`) and service deployment settings.
- Initialized Prometheus monitoring telemetry interfaces.

### 5. Automated workflows, runbooks & bootstrap scripts
- Established first ADR explaining architectural consolidation decisions.
- Created restore operations guides (runbooks) and bootstrap Powershell scripts.
