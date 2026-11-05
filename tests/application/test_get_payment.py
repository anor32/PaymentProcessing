import pytest

from src.application.usecases.get_payment import GetPaymentUseCase
from src.domain.entities.payment import Payment

pytestmark = pytest.mark.asyncio


class TestGetPaymentUseCase:
    async def test_get_payment_returns_existing_with_all_fields(
        self,
        get_payment_usecase: GetPaymentUseCase,
        saved_payment: Payment,
    ) -> None:
        result = await get_payment_usecase.execute(saved_payment.id)

        assert result is not None
        assert isinstance(result, Payment)
        assert result.id == saved_payment.id
        assert result.amount == saved_payment.amount
        assert result.currency == saved_payment.currency
        assert result.status == saved_payment.status
        assert result.idempotency_key == saved_payment.idempotency_key
        assert result.description == saved_payment.description
        assert result.metadata == saved_payment.metadata
        assert result.webhook_url == saved_payment.webhook_url

    async def test_get_payment_not_found_raises(
        self,
        get_payment_usecase: GetPaymentUseCase,
    ) -> None:
        try:
            await get_payment_usecase.execute("non-existent-id")
            raise AssertionError("Expected ObjectNotFoundError")
        except Exception as exc:
            assert type(exc).__name__ == "ObjectNotFoundError"
            assert "not found" in str(exc).lower()
