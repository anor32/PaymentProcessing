from decimal import Decimal
from typing import Any

from src.domain.entities.payment import Payment
from src.domain.value_objects.payment_objects import Currency, PaymentStatus

PAYMENT_ENTITY_DATA: dict[str, Any] = {
    "id": "test-payment-id",
    "amount": Decimal("100.50"),
    "currency": Currency.RUB,
    "description": "Test payment",
    "metadata": {"order_id": "123"},
    "status": PaymentStatus.PENDING,
    "idempotency_key": "test-idem-123",
    "webhook_url": "https://example.com/webhook",
}

PAYMENT_CREATE_DTO_DATA: dict[str, Any] = {
    "amount": Decimal("100.50"),
    "currency": Currency.RUB,
    "description": "Test payment",
    "metadata": {"order_id": "123"},
    "idempotency_key": "test-idem-123",
    "webhook_url": "https://example.com/webhook",
}

PAYMENT_1_DATA: dict[str, Any] = {
    "id": "pay-1",
    "amount": Decimal("100.50"),
    "currency": Currency.RUB,
    "description": "Test payment",
    "metadata": {"order_id": "123"},
    "status": PaymentStatus.PENDING,
    "idempotency_key": "idem-1",
    "webhook_url": "https://example.com/webhook",
}

PAYMENT_2_DATA: dict[str, Any] = {
    "id": "pay-2",
    "amount": Decimal("100.00"),
    "currency": Currency.USD,
    "description": "Test",
    "status": PaymentStatus.SUCCEEDED,
}


def make_payment(**overrides: Any) -> Payment:
    data = {**PAYMENT_ENTITY_DATA, **overrides}
    return Payment(**data)


def make_payment_1(**overrides: Any) -> Payment:
    data = {**PAYMENT_1_DATA, **overrides}
    return Payment(**data)


def make_payment_2(**overrides: Any) -> Payment:
    data = {**PAYMENT_2_DATA, **overrides}
    return Payment(**data)
