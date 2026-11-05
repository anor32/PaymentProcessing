import pytest

from src.domain.entities.payment import Payment
from src.domain.value_objects.payment_objects import Currency
from tests.fakes import FakeUnitOfWork

pytestmark = pytest.mark.asyncio


class TestFakeUnitOfWork:
    async def test_uow_commits_on_success(self, uow: FakeUnitOfWork) -> None:
        async with uow:
            payment = Payment(
                id="pay-uow-1",
                amount=100.00,
                currency=Currency.RUB,
                description="UoW test",
                idempotency_key="idempotency-uow-1",
            )
            await uow.payments.create(payment)

        assert uow.committed is True
        assert uow.rolled_back is False

    async def test_uow_rollbacks_on_error(self, uow: FakeUnitOfWork) -> None:
        try:
            async with uow:
                payment = Payment(
                    id="pay-uow-2",
                    amount=100.00,
                    currency=Currency.RUB,
                    description="Will be rolled back",
                    idempotency_key="idempotency-uow-2",
                )
                await uow.payments.create(payment)
                raise ValueError("Simulated error")
        except ValueError:
            pass

        assert uow.committed is False
        assert uow.rolled_back is True
