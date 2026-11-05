from src.domain.exceptions import (
    AppError,
    IdempotencyError,
    InvalidPaymentError,
    MaxRetriesExceededError,
    ObjectNotFoundError,
    PermanentError,
    RetryableError,
)


class TestDomainExceptions:
    def test_app_error_base(self) -> None:
        exc = AppError("Test error", {"key": "value"})
        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.details == {"key": "value"}

    def test_retryable_error(self) -> None:
        exc = RetryableError("Temporary failure")
        assert isinstance(exc, AppError)
        assert str(exc) == "Temporary failure"

    def test_permanent_error(self) -> None:
        exc = PermanentError("Critical failure")
        assert isinstance(exc, AppError)
        assert str(exc) == "Critical failure"

    def test_max_retries_exceeded_error(self) -> None:
        exc = MaxRetriesExceededError("Max retries")
        assert isinstance(exc, AppError)
        assert str(exc) == "Max retries"

    def test_idempotency_error(self) -> None:
        exc = IdempotencyError("Duplicate key")
        assert isinstance(exc, AppError)
        assert str(exc) == "Duplicate key"

    def test_object_not_found_error(self) -> None:
        exc = ObjectNotFoundError("Payment not found")
        assert isinstance(exc, PermanentError)
        assert isinstance(exc, AppError)
        assert str(exc) == "Payment not found"

    def test_invalid_payment_error(self) -> None:
        exc = InvalidPaymentError("Invalid amount")
        assert isinstance(exc, AppError)
        assert str(exc) == "Invalid amount"

    def test_default_messages(self) -> None:
        assert RetryableError().message == "Временная ошибка. Попробуйте позже."
        assert PermanentError().message == "Произошла критическая ошибка. Повтор не поможет."
        assert MaxRetriesExceededError().message == "Превышено максимальное количество попыток."
        assert IdempotencyError().message == "Нарушена идемпотентность запроса."
        assert ObjectNotFoundError().message == "Запрашиваемый объект не найден."
        assert InvalidPaymentError().message == "Некорректные данные платежа."
