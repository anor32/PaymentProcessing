from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.application.dtos.payment_read_dto import PaymentReadDto
from src.domain.value_objects.payment_objects import Currency


class PaymentCreateRequest(BaseModel):
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    webhook_url: str | None = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("amount must be positive")
        return v

    @field_validator("description")
    @classmethod
    def description_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("description must not be empty")
        return v

    @field_validator("webhook_url")
    @classmethod
    def webhook_url_must_be_valid(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("webhook_url must not be empty if provided")
        return v


class PaymentResponse(PaymentReadDto):
    pass
