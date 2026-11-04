from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from src.domain.exceptions import InvalidPaymentError
from src.domain.value_objects.payment_objects import Currency, PaymentStatus


@dataclass
class Payment:
    id: str
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any]
    status: PaymentStatus
    idempotency_key: str | None
    webhook_url: str | None
    created_at: datetime | None
    processed_at: datetime | None
    error_message: str | None

    def __post_init__(self) -> None:
        _validate_payment(
            amount=self.amount,
            description=self.description,
            idempotency_key=self.idempotency_key,
        )

    def mark_as_succeeded(self) -> None:
        self.status = PaymentStatus.SUCCEEDED

    def mark_as_failed(self, error_message: str | None = None) -> None:
        self.status = PaymentStatus.FAILED
        self.error_message = error_message

    def to_payload(self) -> dict[str, Any]:
        return {
            "payment_id": self.id,
            "amount": str(self.amount),
            "currency": self.currency.value,
            "status": self.status.value,
        }


def _validate_payment(
    *,
    amount: Decimal,
    description: str,
    idempotency_key: str | None,
) -> None:
    if amount <= 0:
        raise InvalidPaymentError("amount must be positive")
    if not description.strip():
        raise InvalidPaymentError("description must not be empty")
    if idempotency_key is not None and not idempotency_key.strip():
        raise InvalidPaymentError("idempotency_key must not be empty if provided")
