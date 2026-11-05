from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from src.application.dtos.payment_read_dto import PaymentReadDto
from src.domain.value_objects.payment_objects import Currency


class PaymentCreateRequest(BaseModel):
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    webhook_url: str | None = None


class PaymentResponse(PaymentReadDto):
    pass
