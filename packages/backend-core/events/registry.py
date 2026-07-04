"""
Event Registry — maps event types to the Celery task names that consume them.

This avoids large if/else chains. Adding a new consumer for an event type
is a single line addition to the REGISTRY dict.
"""
from typing import Dict, List

# Maps event_type -> list of Celery task paths that should process it.
# Each task receives the full DomainEvent dict as its single argument.
REGISTRY: Dict[str, List[str]] = {
    # ── Appointment ───────────────────────────────────────────────────────
    "appointment.created": [
        "queues.notification.handle_event",
        "queues.reminder.handle_event",
        "queues.analytics.handle_event",
    ],
    "appointment.cancelled": [
        "queues.notification.handle_event",
        "queues.analytics.handle_event",
    ],
    "appointment.rescheduled": [
        "queues.notification.handle_event",
        "queues.reminder.handle_event",
        "queues.analytics.handle_event",
    ],

    # ── Consultation ──────────────────────────────────────────────────────
    "consultation.started": [
        "queues.analytics.handle_event",
    ],
    "consultation.completed": [
        "queues.notification.handle_event",
        "queues.analytics.handle_event",
        "queues.ai_worker.handle_event",
    ],

    # ── Prescription ──────────────────────────────────────────────────────
    "prescription.created": [
        "queues.notification.handle_event",
        "queues.reminder.handle_event",
    ],

    # ── Vitals ────────────────────────────────────────────────────────────
    "vital.recorded": [
        "queues.risk_worker.handle_event",
        "queues.analytics.handle_event",
    ],

    # ── Risk / AI ─────────────────────────────────────────────────────────
    "risk.generated": [
        "queues.notification.handle_event",
    ],
}


def get_consumers(event_type: str) -> List[str]:
    """
    Returns the list of Celery task names that should process this event type.
    Returns an empty list for unregistered event types (no-op).
    """
    return REGISTRY.get(event_type, [])
