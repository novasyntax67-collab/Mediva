"""
EventBus — Abstract interface + CeleryEventBus concrete implementation.

The EventBus interface decouples services from the transport layer.
Replacing Celery with Kafka, RabbitMQ, or NATS requires only a new
implementation of EventBus — no service code changes.
"""
from abc import ABC, abstractmethod
from typing import List
import logging

from events.base import DomainEvent
from events.registry import get_consumers

logger = logging.getLogger(__name__)


class EventBus(ABC):
    """
    Abstract transport interface.
    Services never import this directly — it's used by the Outbox Publisher.
    """

    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """Publish a single domain event to registered consumers."""
        ...

    @abstractmethod
    def publish_batch(self, events: List[DomainEvent]) -> None:
        """Publish a batch of events. Implementations may optimize batching."""
        ...


class CeleryEventBus(EventBus):
    """
    Routes events through Celery's send_task interface.
    Each event is dispatched to every consumer registered in the EventRegistry.
    """

    def __init__(self, celery_app):
        self._celery = celery_app

    def publish(self, event: DomainEvent) -> None:
        consumers = get_consumers(event.event_type)
        event_dict = event.to_dict()

        if not consumers:
            logger.warning(
                "No consumers registered for event_type=%s event_id=%s",
                event.event_type,
                event.event_id,
            )
            return

        for task_name in consumers:
            try:
                self._celery.send_task(task_name, args=[event_dict])
                logger.info(
                    "Dispatched event_id=%s type=%s -> %s",
                    event.event_id,
                    event.event_type,
                    task_name,
                )
            except Exception as exc:
                logger.error(
                    "Failed to dispatch event_id=%s to %s: %s",
                    event.event_id,
                    task_name,
                    exc,
                )
                raise  # Let the outbox publisher handle retries

    def publish_batch(self, events: List[DomainEvent]) -> None:
        """Publish a list of events in commit order."""
        for event in events:
            self.publish(event)
