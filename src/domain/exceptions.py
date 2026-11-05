from typing import Any


class AppError(Exception):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        return self.message


class RetryableError(AppError):
    def __init__(
        self,
        message: str = "Временная ошибка. Попробуйте позже.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details)


class PermanentError(AppError):
    def __init__(
        self,
        message: str = "Произошла критическая ошибка. Повтор не поможет.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details)


class MaxRetriesExceededError(AppError):
    def __init__(
        self,
        message: str = "Превышено максимальное количество попыток.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details)


class IdempotencyError(AppError):
    def __init__(
        self,
        message: str = "Нарушена идемпотентность запроса.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details)


class ObjectNotFoundError(PermanentError):
    def __init__(
        self,
        message: str = "Запрашиваемый объект не найден.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details)


class InvalidPaymentError(AppError):
    def __init__(
        self,
        message: str = "Некорректные данные платежа.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details)
