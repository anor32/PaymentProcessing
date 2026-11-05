import pytest

from src.domain.entities.payment import Payment
from src.domain.value_objects.payment_objects import PaymentStatus
from tests.fakes import FakePaymentRepository

pytestmark = pytest.mark.asyncio


class TestFakePaymentRepository:
    async def test_create_and_get_by_id(
        self,
        payment_repo: FakePaymentRepository,
        payment_entity: Payment,
    ) -> None:
        created = await payment_repo.create(payment_entity)

        assert created.id == payment_entity.id
        assert created.amount == payment_entity.amount

        retrieved = await payment_repo.get_by_id(payment_entity.id)

        assert retrieved is not None
        assert retrieved.id == payment_entity.id
        assert retrieved.status == payment_entity.status

    async def test_get_by_id_not_found(
        self,
        payment_repo: FakePaymentRepository,
    ) -> None:
        result = await payment_repo.get_by_id("non-existent")

        assert result is None

    async def test_update_payment(
        self,
        payment_repo: FakePaymentRepository,
        payment_entity: Payment,
    ) -> None:
        await payment_repo.create(payment_entity)

        payment_entity.mark_as_succeeded()
        updated = await payment_repo.update(payment_entity)

        assert updated is not None
        assert updated.status == PaymentStatus.SUCCEEDED

        retrieved = await payment_repo.get_by_id(payment_entity.id)
        assert retrieved is not None
        assert retrieved.status == PaymentStatus.SUCCEEDED

    async def test_update_not_found(
        self,
        payment_repo: FakePaymentRepository,
        payment_entity: Payment,
    ) -> None:
        result = await payment_repo.update(payment_entity)

        assert result is None
