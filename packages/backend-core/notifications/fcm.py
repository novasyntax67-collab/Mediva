"""
FCM Provider — Firebase Cloud Messaging push notification integration.

Implements MockFCMProvider for developer testing and local execution:
  - Simulates sending FCM push messages to client device tokens.
  - Supports custom notification data payload dictionaries.
  - Returns FCM message ID strings and status responses.
  - Keeps an in-memory log of dispatched push notifications for unit test verification.
"""
import uuid
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from notifications.provider import NotificationProvider, NotificationChannel, DeliveryResult

logger = logging.getLogger(__name__)


@dataclass
class MockPushMessage:
    """Record of a simulated FCM push notification."""
    message_id: str
    token: str
    title: str
    body: str
    data: Optional[Dict[str, Any]] = None


class MockFCMProvider(NotificationProvider):
    """
    Simulates Firebase Cloud Messaging (FCM) v1 HTTP API client.
    """

    def __init__(self, service_account_info: Optional[Dict[str, Any]] = None):
        self.service_account_info = service_account_info
        # In-memory log of dispatched messages
        self.sent_messages: List[MockPushMessage] = []

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.PUSH

    def send(
        self,
        recipient: str,
        title: str,
        body: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DeliveryResult:
        """
        Simulates sending a push notification via FCM.

        recipient: The FCM device registration token.
        """
        # Generate a standard Firebase message ID format: projects/project-id/messages/0:162...
        message_id = f"projects/mediva-health/messages/0:{uuid.uuid4().hex[:16]}"

        push_msg = MockPushMessage(
            message_id=message_id,
            token=recipient,
            title=title,
            body=body,
            data=metadata,
        )
        self.sent_messages.append(push_msg)

        logger.info(
            "🔔 MOCK FCM PUSH [SENT] ID=%s token=%s | %s: %s (data=%s)",
            message_id, recipient[:15] + "...", title, body[:60], metadata
        )

        return DeliveryResult(
            success=True,
            provider_message_id=message_id,
            provider_response={
                "name": message_id,
                "token": recipient,
                "notification": {
                    "title": title,
                    "body": body,
                },
                "data": metadata or {},
            },
        )

    def get_message_log(self) -> List[Dict[str, Any]]:
        return [
            {
                "message_id": m.message_id,
                "token": m.token,
                "title": m.title,
                "body": m.body,
                "data": m.data,
            }
            for m in self.sent_messages
        ]

    def clear_log(self):
        self.sent_messages.clear()
