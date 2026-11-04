from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from src.domain.value_objects.payment_objects import Currency, PaymentStatus


class PaymentReadDto(BaseModel):
    """DTO для чтения данных платежа."""

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
