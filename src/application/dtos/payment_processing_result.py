"""Результат выполнения ProcessPaymentUseCase."""

from dataclasses import dataclass
from enum import StrEnum


class PaymentProcessingAction(StrEnum):
    SUCCESS = "success"
    RETRY = "retry"
    DLQ = "dlq"


@dataclass
class PaymentProcessingResult:
    action: PaymentProcessingAction
    target_queue: str | None = None
    retry_count: int = 0
    error_message: str | None = None
