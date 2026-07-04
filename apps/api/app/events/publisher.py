"""
Event Publisher — API-layer bridge to the Outbox Publisher.

In this architecture, events are NOT published directly from the API.
Instead, services call `uow.collect_event()` to register domain events,
and the UnitOfWork persists them into the `event_outbox` table atomically
on commit (Transactional Outbox Pattern).

The actual publishing is handled by the Outbox Publisher worker
(apps/worker/queues/outbox_publisher.py), which polls the outbox table
and dispatches events through the EventBus interface to Celery workers.

Flow:
    Service → uow.collect_event(event)
    UoW.commit() → INSERT INTO event_outbox (same transaction)
    Outbox Publisher (Beat, 5s) → SELECT pending → EventBus.publish()
    CeleryEventBus → Redis → Worker tasks

This module exists as documentation. Direct publishing from the API
layer is intentionally not supported to prevent the "commit succeeded
but Redis was down" failure mode.
"""
