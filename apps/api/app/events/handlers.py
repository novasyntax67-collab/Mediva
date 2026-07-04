"""
Event Handlers — maps domain events to side-effect actions within the API.

In production, event handling is done by background Celery workers
(apps/worker/queues/), NOT within the API process. This ensures:

  1. API responses remain fast (no blocking on notifications, analytics, etc.)
  2. Side effects retry independently via the worker retry mechanism.
  3. The API process stays focused on request handling.

Worker Responsibilities:
  ┌─────────────────┬──────────────────────────────────────────────────┐
  │ Worker          │ Consumes                                         │
  ├─────────────────┼──────────────────────────────────────────────────┤
  │ Notification    │ appointment.created, consultation.completed,     │
  │                 │ prescription.created, risk.generated             │
  ├─────────────────┼──────────────────────────────────────────────────┤
  │ Reminder        │ appointment.created, appointment.rescheduled,    │
  │                 │ prescription.created                             │
  ├─────────────────┼──────────────────────────────────────────────────┤
  │ Analytics       │ appointment.*, consultation.*, vital.recorded    │
  ├─────────────────┼──────────────────────────────────────────────────┤
  │ Risk            │ vital.recorded                                   │
  ├─────────────────┼──────────────────────────────────────────────────┤
  │ AI              │ consultation.completed                           │
  └─────────────────┴──────────────────────────────────────────────────┘

See: packages/backend-core/events/registry.py for the full routing map.
"""
