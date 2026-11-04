from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from src.domain.value_objects.payment_objects import Currency, PaymentStatus


@dataclass
class Payment:
    id: str
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)
    status: PaymentStatus = PaymentStatus.PENDING
    idempotency_key: str | None = None
    webhook_url: str | None = None
    created_at: datetime | None = None
    processed_at: datetime | None = None
    error_message: str | None = None

    def mark_as_succeeded(self) -> None:
        self.status = PaymentStatus.SUCCEEDED

    def mark_as_failed(self, error_message: str | None = None) -> None:
        self.status = PaymentStatus.FAILED
        self.error_message = error_message
