from sqlalchemy.ext.asyncio import AsyncSession
from typing import Self, List
import uuid
import logging

from events.base import DomainEvent

logger = logging.getLogger(__name__)


class UnitOfWork:
    """
    Coordinates atomic transactional operations across multiple repositories.

    Event-driven design:
      - Services call collect_event() to register domain events.
      - On commit(), pending events are inserted into the event_outbox table
        INSIDE the same PostgreSQL transaction as the clinical records.
      - On rollback(), the pending list is cleared — no outbox rows are created.
      - The Outbox Publisher worker polls the outbox and dispatches to Celery.

    This implements the Transactional Outbox Pattern, guaranteeing that if the
    clinical record exists, the event also exists. No event is ever lost due
    to a Redis outage after commit.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._pending_events: List[DomainEvent] = []

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
            await self.rollback()
        else:
            await self.commit()

    def collect_event(self, event: DomainEvent) -> None:
        """
        Register a domain event to be persisted in the outbox on commit.
        Services use this instead of mutating the event list directly.
        Events are published in the order they are collected (commit order).
        """
        self._pending_events.append(event)

    async def commit(self) -> None:
        """
        Inserts all pending events into the event_outbox table and then
        commits the entire transaction atomically.
        """
        # Import here to avoid circular imports at module level
        from database.models import EventOutbox

        for event in self._pending_events:
            outbox_row = EventOutbox(
                id=uuid.UUID(event.event_id),
                event_type=event.event_type,
                event_version=event.event_version,
                aggregate_type=event.aggregate_type,
                aggregate_id=uuid.UUID(event.aggregate_id),
                payload=event.to_dict(),
                actor_id=uuid.UUID(event.actor_id),
                tenant_id=uuid.UUID(event.tenant_id) if event.tenant_id else None,
                correlation_id=uuid.UUID(event.correlation_id) if event.correlation_id else None,
                causation_id=uuid.UUID(event.causation_id) if event.causation_id else None,
                status="pending",
            )
            self.session.add(outbox_row)

        await self.session.commit()

        if self._pending_events:
            logger.info(
                "Committed transaction with %d outbox event(s): %s",
                len(self._pending_events),
                [e.event_type for e in self._pending_events],
            )

        self._pending_events.clear()

    async def rollback(self) -> None:
        """Roll back the transaction and discard all pending events."""
        await self.session.rollback()
        discarded = len(self._pending_events)
        self._pending_events.clear()
        if discarded:
            logger.info("Rolled back transaction, discarded %d pending event(s)", discarded)

    async def flush(self) -> None:
        await self.session.flush()
