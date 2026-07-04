"""
Mock Twilio Provider — Simulates SMS/voice delivery for development.

Behaves identically to a real Twilio integration:
  - Generates fake SIDs (SM + 32 hex chars)
  - Logs messages to console and an in-memory ledger
  - Simulates delivery latency (configurable)
  - Supports configurable failure rate for testing retry logic
  - Returns DeliveryResult matching the real provider contract

The in-memory ledger (MockTwilioProvider.sent_messages) lets tests
assert on what would have been sent without hitting any external API.
"""
import uuid
import time
import random
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from notifications.provider import NotificationProvider, NotificationChannel, DeliveryResult

logger = logging.getLogger(__name__)


@dataclass
class MockSMSMessage:
    """Record of a simulated SMS delivery."""
    sid: str
    to: str
    from_: str
    body: str
    status: str  # queued, sent, delivered, failed
    created_at: float
    metadata: Optional[Dict[str, Any]] = None


class MockTwilioProvider(NotificationProvider):
    """
    Drop-in replacement for Twilio's REST API client.

    Usage:
        provider = MockTwilioProvider(
            account_sid="AC_test",
            auth_token="test_token",
            from_number="+15551234567",
            failure_rate=0.0,       # 0% failure for deterministic tests
            latency_ms=0,           # No simulated delay
        )
        result = provider.send("+15559876543", "Reminder", "Your appointment is tomorrow.")
    """

    def __init__(
        self,
        account_sid: str = "AC_mock_test_account",
        auth_token: str = "mock_auth_token",
        from_number: str = "+15551234567",
        failure_rate: float = 0.0,
        latency_ms: int = 0,
    ):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.failure_rate = failure_rate
        self.latency_ms = latency_ms

        # In-memory ledger — tests can inspect this
        self.sent_messages: List[MockSMSMessage] = []

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.SMS

    def send(
        self,
        recipient: str,
        title: str,
        body: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DeliveryResult:
        """
        Simulate sending an SMS via Twilio.

        The title is prepended to the body since SMS doesn't have a subject field.
        """
        # Simulate network latency
        if self.latency_ms > 0:
            time.sleep(self.latency_ms / 1000.0)

        # Generate a Twilio-style SID
        sid = f"SM{uuid.uuid4().hex}"

        # Simulate configurable failure rate
        if random.random() < self.failure_rate:
            message = MockSMSMessage(
                sid=sid,
                to=recipient,
                from_=self.from_number,
                body=f"[{title}] {body}",
                status="failed",
                created_at=time.time(),
                metadata=metadata,
            )
            self.sent_messages.append(message)

            logger.warning(
                "📱 MOCK TWILIO [FAILED] SID=%s to=%s | %s",
                sid, recipient, title
            )
            return DeliveryResult(
                success=False,
                provider_message_id=sid,
                provider_response={
                    "sid": sid,
                    "status": "failed",
                    "error_code": 30006,
                    "error_message": "Simulated delivery failure (mock)",
                },
                error_message="Simulated delivery failure",
            )

        # Successful delivery
        message = MockSMSMessage(
            sid=sid,
            to=recipient,
            from_=self.from_number,
            body=f"[{title}] {body}",
            status="delivered",
            created_at=time.time(),
            metadata=metadata,
        )
        self.sent_messages.append(message)

        logger.info(
            "📱 MOCK TWILIO [DELIVERED] SID=%s to=%s | %s: %s",
            sid, recipient, title, body[:80]
        )

        return DeliveryResult(
            success=True,
            provider_message_id=sid,
            provider_response={
                "sid": sid,
                "status": "delivered",
                "to": recipient,
                "from": self.from_number,
                "body": f"[{title}] {body}",
                "num_segments": max(1, len(body) // 160 + 1),
                "price": "-0.0075",
                "price_unit": "USD",
            },
        )

    def get_message_log(self) -> List[Dict[str, Any]]:
        """Return the full in-memory message ledger for testing assertions."""
        return [
            {
                "sid": m.sid,
                "to": m.to,
                "from": m.from_,
                "body": m.body,
                "status": m.status,
                "metadata": m.metadata,
            }
            for m in self.sent_messages
        ]

    def clear_log(self):
        """Clear the message ledger between test runs."""
        self.sent_messages.clear()
