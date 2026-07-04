"""
Event Consumer — not used in the API layer.

Event consumption happens in the worker process (apps/worker/queues/).
Each worker implements an idempotent `handle_event(event_dict)` task that:

  1. Checks the `processed_events` table for duplicates (idempotency guard).
  2. Processes the event payload.
  3. Marks the event as processed in `processed_events`.

The Outbox Publisher (apps/worker/queues/outbox_publisher.py) dispatches
events from the `event_outbox` table through the EventBus interface to
the registered Celery task consumers defined in the EventRegistry
(packages/backend-core/events/registry.py).
"""
