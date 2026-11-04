from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from pydantic import BaseModel

from src.domain.entities.payment import Payment
from src.domain.value_objects.payment_objects import Currency, PaymentStatus


class PaymentCreateDto(BaseModel):
    """DTO для создания нового платежа."""

    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any] = {}
    idempotency_key: str | None = None
    webhook_url: str | None = None

    def to_entity(self) -> Payment:
        """Преобразует DTO в доменную сущность Payment."""
        return Payment(
            id=str(uuid4()),
            amount=self.amount,
            currency=self.currency,
            description=self.description,
            metadata=self.metadata,
            status=PaymentStatus.PENDING,
            idempotency_key=self.idempotency_key,
            webhook_url=self.webhook_url,
            created_at=datetime.now(UTC),
        )
