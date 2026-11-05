from dataclasses import dataclass, field
from typing import Any

from src.domain.entities.payment import Payment
from src.domain.value_objects.payment_objects import PaymentStatus
from src.infrastructure.database.models import OutboxEventType


@dataclass
class OutboxEventDto:
    """DTO for Outbox event."""

    id: str | None = None
    event_type: OutboxEventType | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def entity_to_dto(cls, payment: Payment) -> OutboxEventDto:
        """Converts Payment entity to Outbox event DTO."""
        event_type = OutboxEventType.PAYMENT_CREATED
        if payment.status == PaymentStatus.SUCCEEDED:
            event_type = OutboxEventType.PAYMENT_SUCCEEDED
        elif payment.status == PaymentStatus.FAILED:
            event_type = OutboxEventType.PAYMENT_FAILED

        return cls(event_type=event_type, payload=payment.to_payload())
