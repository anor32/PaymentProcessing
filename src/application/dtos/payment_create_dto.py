from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Self
from uuid import uuid4

from pydantic import BaseModel, Field

from src.domain.entities.payment import Payment
from src.domain.value_objects.payment_objects import Currency, PaymentStatus
from src.presentation.schemas.payment_schemas import PaymentCreateRequest


class PaymentCreateDto(BaseModel):
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None
    webhook_url: str | None = None

    @classmethod
    def from_request(
        cls,
        request: PaymentCreateRequest,
        idempotency_key: str,
    ) -> Self:
        return cls(
            amount=request.amount,
            currency=request.currency,
            description=request.description,
            metadata=request.metadata,
            idempotency_key=idempotency_key,
            webhook_url=request.webhook_url,
        )

    def to_entity(self) -> Payment:
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
            processed_at=None,
            error_message=None,
        )
