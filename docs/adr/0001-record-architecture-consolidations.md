# ADR 0001: Consolidated AI Service & Celery Worker

## Context
Initial specifications proposed splitting the AI gateway, triage system, report summarizer, and anomaly detection models, as well as multiple worker channels, into independent deployable microservices. 

## Decision
We decided to consolidate the AI functionalities into a single `apps/ai-service` and background jobs into `apps/worker` while maintaining distinct module boundaries internally.

## Consequences
- Operational complexity is reduced: 2 services to deploy instead of 10.
- Resource allocation and monitoring are simplified.
- Code maintains logical separation allowing extraction later.
