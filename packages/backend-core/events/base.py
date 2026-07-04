"""
Domain Event Envelope — Versioned, traceable event schema.

Every domain event in the system uses this envelope format. It includes:
- event_id:        Unique identifier (UUID4) for deduplication.
- event_type:      Past-tense dot-notation name (e.g. "appointment.created").
- event_version:   Schema version for forward-compatible evolution.
- occurred_at:     ISO 8601 timestamp when the event was produced.
- aggregate_type:  The domain aggregate that produced this event (e.g. "appointment").
- aggregate_id:    The primary key of that aggregate instance.
- correlation_id:  Groups related events across a workflow (e.g. a booking flow).
- causation_id:    The event_id of the event that caused this one (tracing chains).
- tenant_id:       Organization scoping for multi-tenant isolation.
- actor_id:        The profile that triggered the action.
- payload:         Lightweight dict of IDs — workers load full data themselves.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import uuid


@dataclass(frozen=True)
class DomainEvent:
    """Immutable domain event envelope."""

    event_type: str
    aggregate_type: str
    aggregate_id: str
    actor_id: str
    payload: Dict[str, Any]

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_version: int = 1
    occurred_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # Tracing / correlation
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None

    # Multi-tenant scoping
    tenant_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dict suitable for JSONB storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainEvent":
        """Reconstruct a DomainEvent from a dict (e.g. from JSONB)."""
        return cls(**data)
