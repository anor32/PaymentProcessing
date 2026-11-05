from datetime import datetime
from decimal import Decimal

import pytest

from src.domain.entities.payment import Payment
from src.domain.exceptions import InvalidPaymentError
from src.domain.value_objects.payment_objects import Currency, PaymentStatus


class TestPaymentEntity:
    def test_create_payment_entity(self) -> None:
        payment = Payment(
            id="pay-1",
            amount=Decimal("100.50"),
            currency=Currency.RUB,
            description="Test payment",
            metadata={"order_id": "123"},
            status=PaymentStatus.PENDING,
            idempotency_key="idem-1",
            webhook_url="https://example.com/webhook",
            created_at=datetime(2026, 11, 5, 12, 0, 0),
            processed_at=None,
        )

        assert payment.id == "pay-1"
        assert payment.amount == Decimal("100.50")
        assert payment.currency == Currency.RUB
        assert payment.status == PaymentStatus.PENDING
        assert payment.idempotency_key == "idem-1"

    def test_mark_as_succeeded(self) -> None:
        payment = Payment(
            id="pay-1",
            amount=Decimal("100.00"),
            currency=Currency.USD,
            description="Test",
            status=PaymentStatus.PENDING,
        )

        payment.mark_as_succeeded()

        assert payment.status == PaymentStatus.SUCCEEDED

    def test_mark_as_failed(self) -> None:
        payment = Payment(
            id="pay-1",
            amount=Decimal("100.00"),
            currency=Currency.USD,
            description="Test",
            status=PaymentStatus.PENDING,
        )

        payment.mark_as_failed(error_message="Insufficient funds")

        assert payment.status == PaymentStatus.FAILED
        assert payment.error_message == "Insufficient funds"

    def test_to_payload(self) -> None:
        payment = Payment(
            id="pay-1",
            amount=Decimal("100.50"),
            currency=Currency.RUB,
            description="Test",
            status=PaymentStatus.SUCCEEDED,
            processed_at=datetime(2026, 11, 5, 12, 30, 0),
            error_message=None,
        )

        payload = payment.to_payload()

        assert payload["payment_id"] == "pay-1"
        assert payload["amount"] == "100.50"
        assert payload["currency"] == "RUB"
        assert payload["status"] == "succeeded"
        assert payload["processed_at"] == "2026-11-05T12:30:00"

    def test_validation_amount_must_be_positive(self) -> None:
        with pytest.raises(InvalidPaymentError, match="amount must be positive"):
            Payment(
                id="pay-1",
                amount=Decimal("0"),
                currency=Currency.RUB,
                description="Test",
            )

    def test_validation_description_must_not_be_empty(self) -> None:
        with pytest.raises(InvalidPaymentError, match="description must not be empty"):
            Payment(
                id="pay-1",
                amount=Decimal("100.00"),
                currency=Currency.RUB,
                description="   ",
            )

    def test_validation_idempotency_key_must_not_be_empty(self) -> None:
        with pytest.raises(InvalidPaymentError, match="idempotency_key must not be empty"):
            Payment(
                id="pay-1",
                amount=Decimal("100.00"),
                currency=Currency.RUB,
                description="Test",
                idempotency_key="   ",
            )
