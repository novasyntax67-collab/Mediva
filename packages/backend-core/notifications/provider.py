"""
Notification Provider — Abstract interface for delivery channels.

Concrete implementations:
  - MockTwilioProvider (development/testing)
  - TwilioProvider     (production, future)
  - ResendProvider     (production email, future)
  - FCMProvider        (production push, future)
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class NotificationChannel(str, Enum):
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"


@dataclass
class DeliveryResult:
    """Result returned by a notification provider after a send attempt."""
    success: bool
    provider_message_id: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class NotificationProvider(ABC):
    """Abstract interface for notification delivery channels."""

    @property
    @abstractmethod
    def channel(self) -> NotificationChannel:
        """The delivery channel this provider handles."""
        ...

    @abstractmethod
    def send(
        self,
        recipient: str,
        title: str,
        body: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DeliveryResult:
        """
        Send a notification to a single recipient.

        Args:
            recipient: Phone number (SMS), email address (Email), or device token (Push).
            title: Notification title/subject.
            body: Notification body content.
            metadata: Optional extra data (template vars, deep links, etc.)

        Returns:
            DeliveryResult with success status and provider details.
        """
        ...
