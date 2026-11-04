from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import DateTime, Enum, Index, Integer, Numeric, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from domain.value_objects.payment_objects import Currency, PaymentStatus


class Base(DeclarativeBase):
    pass


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(primary_key=True)
    amount: Mapped[Decimal] = mapped_column(Numeric)
    currency: Mapped[Currency] = mapped_column(Enum(Currency, name="currency_enum"))
    description: Mapped[str] = mapped_column(String(1000))

    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status_enum"), default=PaymentStatus.PENDING
    )

    idempotency_key: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    webhook_url: Mapped[str] = mapped_column(String(1000))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(String(500))


class OutboxEventType(StrEnum):
    PAYMENT_CREATED = "payment.created"
    PAYMENT_SUCCEEDED = "payment.succeeded"
    PAYMENT_FAILED = "payment.failed"


class OutboxStatus(StrEnum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"


class Outbox(Base):
    __tablename__ = "outbox"

    (
        Index(
            "ix_outbox_published_at_not_null",
            "published_at",
            postgresql_where=text("published_at IS NOT NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(primary_key=True, default=func.gen_random_uuid())
    event_type: Mapped[OutboxEventType]
    payload: Mapped[dict] = mapped_column(JSONB)

    status: Mapped[OutboxStatus] = mapped_column(
        Enum(OutboxStatus, name="outbox_status_enum"), default=OutboxStatus.PENDING
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(String(500))
