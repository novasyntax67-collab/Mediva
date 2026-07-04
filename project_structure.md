# Carex Project Structure

Below is the directory map of the Carex monorepo (excluding dependency directories like `node_modules`, `.venv`, and build caches).

```text
Carex/
├── .github/
│   └── workflows/
│       ├── backend.yml
│       ├── frontend.yml
│       └── security.yml
│
├── apps/
│   ├── ai-service/
│   │   ├── gateway/
│   │   │   └── router.py
│   │   ├── anomaly/
│   │   ├── embeddings/
│   │   ├── medication/
│   │   ├── rag/
│   │   ├── report/
│   │   ├── shared/
│   │   ├── triage/
│   │   ├── main.py
│   │   └── requirements.txt
│   │
│   ├── api/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   └── v1/
│   │   │   │       └── routers/
│   │   │   │           └── patients.py
│   │   │   │
│   │   │   ├── common/
│   │   │   │   ├── base_model.py
│   │   │   │   ├── constants.py
│   │   │   │   ├── enums.py
│   │   │   │   ├── mixins.py
│   │   │   │   └── types.py
│   │   │   │
│   │   │   ├── core/
│   │   │   │   ├── config.py
│   │   │   │   ├── database.py
│   │   │   │   ├── dependencies.py
│   │   │   │   ├── logging.py
│   │   │   │   ├── middleware.py
│   │   │   │   ├── redis.py
│   │   │   │   ├── security.py
│   │   │   │   ├── supabase.py
│   │   │   │   └── telemetry.py
│   │   │   │
│   │   │   ├── events/
│   │   │   │   ├── base.py
│   │   │   │   ├── consumer.py
│   │   │   │   ├── handlers.py
│   │   │   │   ├── publisher.py
│   │   │   │   └── types.py
│   │   │   │
│   │   │   ├── modules/
│   │   │   │   ├── appointments/
│   │   │   │   ├── audit/
│   │   │   │   ├── auth/
│   │   │   │   ├── consent/
│   │   │   │   ├── consultation/
│   │   │   │   ├── notifications/
│   │   │   │   ├── patients/
│   │   │   │   │   ├── events.py
│   │   │   │   │   ├── models.py
│   │   │   │   │   ├── permissions.py
│   │   │   │   │   ├── repository.py
│   │   │   │   │   ├── schemas.py
│   │   │   │   │   ├── service.py
│   │   │   │   │   └── validators.py
│   │   │   │   ├── shared/
│   │   │   │   └── vitals/
│   │   │   └── main.py
│   │   ├── pyproject.toml
│   │   └── requirements.txt
│   │
│   ├── web/
│   │   ├── src/
│   │   │   └── app/
│   │   │       ├── (admin)/
│   │   │       ├── (api)/
│   │   │       ├── (auth)/
│   │   │       ├── (caregiver)/
│   │   │       ├── (clinician)/
│   │   │       ├── (patient)/
│   │   │       ├── dashboard/
│   │   │       ├── globals.css
│   │   │       ├── layout.tsx
│   │   │       └── page.tsx
│   │   ├── next.config.js
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── worker/
│       ├── queues/
│       │   ├── analytics.py
│       │   ├── cleanup.py
│       │   ├── emails.py
│       │   ├── notification.py
│       │   ├── reminder.py
│       │   └── vitals.py
│       ├── beat.py
│       ├── celery_app.py
│       └── requirements.txt
│
├── configs/
│   ├── development/
│   │   └── config.yaml
│   ├── docker/
│   │   └── config.yaml
│   ├── production/
│   │   └── config.yaml
│   └── staging/
│       └── config.yaml
│
├── database/
│   ├── functions/
│   ├── migrations/
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── policies/
│   ├── seed/
│   ├── triggers/
│   ├── views/
│   └── alembic.ini
│
├── docs/
│   ├── adr/
│   │   └── 0001-record-architecture-consolidations.md
│   ├── architecture/
│   └── runbooks/
│       └── database-restore.md
│
├── infrastructure/
│   ├── docker/
│   │   ├── api/
│   │   │   └── Dockerfile
│   │   ├── ai/
│   │   │   └── Dockerfile
│   │   ├── base/
│   │   │   ├── gpu/
│   │   │   │   └── Dockerfile
│   │   │   ├── node/
│   │   │   │   └── Dockerfile
│   │   │   └── python/
│   │   │       └── Dockerfile
│   │   ├── web/
│   │   │   └── Dockerfile
│   │   └── worker/
│   │       └── Dockerfile
│   ├── dokploy/
│   │   ├── api.yaml
│   │   ├── livekit.yaml
│   │   ├── web.yaml
│   │   └── worker.yaml
│   └── monitoring/
│       ├── prometheus/
│       │   └── prometheus.yml
│       └── (grafana, loki, otel, tracing, dashboards, alerts)
│
├── logs/
│   └── walkthrough.md
│
├── models/
│   ├── embeddings/
│   ├── ocr/
│   ├── onnx/
│   └── triage/
│
├── packages/
│   ├── auth/
│   │   ├── src/
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   ├── backend-core/
│   │   ├── auth/
│   │   │   └── __init__.py
│   │   ├── config/
│   │   │   └── __init__.py
│   │   ├── database/
│   │   │   └── __init__.py
│   │   ├── events/
│   │   │   └── __init__.py
│   │   ├── exceptions/
│   │   │   └── __init__.py
│   │   ├── logging/
│   │   │   └── __init__.py
│   │   ├── metrics/
│   │   │   └── __init__.py
│   │   ├── security/
│   │   │   └── __init__.py
│   │   ├── utils/
│   │   │   └── __init__.py
│   │   └── pyproject.toml
│   ├── config/
│   │   └── package.json
│   ├── healthcare/
│   │   ├── coding/
│   │   ├── fhir/
│   │   ├── hl7/
│   │   ├── terminology/
│   │   ├── validators/
│   │   ├── src/
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   ├── sdk/
│   │   ├── python/
│   │   ├── typescript/
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   ├── types/
│   │   ├── src/
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   ├── ui/
│   │   ├── src/
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── validation/
│       ├── src/
│       │   └── index.ts
│       ├── package.json
│       └── tsconfig.json
│
├── scripts/
│   ├── backup/
│   ├── bootstrap/
│   │   └── setup.ps1
│   ├── generate-env/
│   ├── migration/
│   ├── restore/
│   └── seed/
│
├── tests/
│   ├── ai/
│   ├── backend/
│   ├── e2e/
│   ├── fixtures/
│   ├── frontend/
│   ├── integration/
│   └── performance/
│
├── .env.api.example
├── .env.example
├── .env.web.example
├── .env.worker.example
├── .env.ai.example
├── docker-compose.yml
├── Makefile
├── package.json
├── pnpm-workspace.yaml
└── tsconfig.json
```
