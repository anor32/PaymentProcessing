import asyncio
from decimal import Decimal

import pytest

from src.application.dtos.payment_create_dto import PaymentCreateDto
from src.application.usecases.create_payment import CreatePaymentUseCase
from src.domain.entities.payment import Payment
from src.domain.interfaces.unit_of_work import IUnitOfWork
from src.domain.value_objects.payment_objects import Currency, PaymentStatus


class TestCreatePaymentUseCase:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "amount,currency,status",
        [
            (Decimal("100.50"), Currency.RUB, PaymentStatus.PENDING),
            (Decimal("200.00"), Currency.USD, PaymentStatus.PENDING),
            (Decimal("50.00"), Currency.EUR, PaymentStatus.PENDING),
        ],
    )
    async def test_create_payment_success(
        self,
        create_payment_usecase: CreatePaymentUseCase,
        payment_create_dto: PaymentCreateDto,
        amount: Decimal,
        currency: Currency,
        status: PaymentStatus,
    ) -> None:
        dto = PaymentCreateDto(
            amount=amount,
            currency=currency,
            description=payment_create_dto.description,
            metadata=payment_create_dto.metadata,
            idempotency_key="idem-1",
            webhook_url=payment_create_dto.webhook_url,
        )

        result = await create_payment_usecase.execute(dto)

        assert isinstance(result, Payment)
        assert result.amount == amount
        assert result.currency == currency
        assert result.status == status
        assert result.idempotency_key == "idem-1"

    @pytest.mark.asyncio
    async def test_create_payment_saves_in_uow(
        self,
        create_payment_usecase: CreatePaymentUseCase,
        uow: IUnitOfWork,
        payment_create_dto: PaymentCreateDto,
    ) -> None:
        dto = PaymentCreateDto(
            amount=Decimal("200.00"),
            currency=Currency.USD,
            description="USD payment",
            idempotency_key="idem-usd",
        )

        result = await create_payment_usecase.execute(dto)

        async with uow:
            saved = await uow.payments.get_by_id(result.id)
            assert saved is not None
            assert saved.id == result.id
            assert saved.amount == Decimal("200.00")
            assert saved.currency == Currency.USD

    @pytest.mark.asyncio
    async def test_create_payment_outbox_event(
        self,
        create_payment_usecase: CreatePaymentUseCase,
        uow: IUnitOfWork,
        payment_create_dto: PaymentCreateDto,
    ) -> None:
        dto = PaymentCreateDto(
            amount=Decimal("50.00"),
            currency=Currency.EUR,
            description="EUR payment",
            idempotency_key="idem-eur",
        )

        await create_payment_usecase.execute(dto)

        async with uow:
            events = await uow.outbox.get_pending_events(limit=10)
            assert len(events) == 1
            assert events[0]["event_type"] == "payment.created"
            assert events[0]["payload"]["payment_id"] is not None
            assert events[0]["payload"]["amount"] == "50.00"

    @pytest.mark.asyncio
    async def test_create_payment_idempotency_key_saved(
        self,
        create_payment_usecase: CreatePaymentUseCase,
        uow: IUnitOfWork,
        payment_create_dto: PaymentCreateDto,
    ) -> None:
        dto = PaymentCreateDto(
            amount=Decimal("100.00"),
            currency=Currency.RUB,
            description="Idempotent payment",
            idempotency_key="unique-idem-key",
        )

        result = await create_payment_usecase.execute(dto)

        async with uow:
            saved = await uow.payments.get_by_id(result.id)
            assert saved is not None
            assert saved.idempotency_key == "unique-idem-key"

    @pytest.mark.asyncio
    async def test_create_payment_idempotent_same_key_returns_existing(
        self,
        create_payment_usecase: CreatePaymentUseCase,
        uow: IUnitOfWork,
    ) -> None:
        dto1 = PaymentCreateDto(
            amount=Decimal("100.00"),
            currency=Currency.RUB,
            description="First payment",
            idempotency_key="idem-same-key",
        )
        dto2 = PaymentCreateDto(
            amount=Decimal("200.00"),
            currency=Currency.USD,
            description="Second payment (same key)",
            idempotency_key="idem-same-key",
        )

        first = await create_payment_usecase.execute(dto1)
        second = await create_payment_usecase.execute(dto2)

        assert second.id == first.id
        assert second.amount == first.amount
        assert second.currency == first.currency
        assert second.description == first.description

        async with uow:
            payments_by_id = await uow.payments.get_by_id(first.id)
            assert payments_by_id is not None
            assert payments_by_id.idempotency_key == "idem-same-key"

    @pytest.mark.asyncio
    async def test_create_payment_idempotent_different_keys_create_separate(
        self,
        create_payment_usecase: CreatePaymentUseCase,
        uow: IUnitOfWork,
    ) -> None:
        dto1 = PaymentCreateDto(
            amount=Decimal("100.00"),
            currency=Currency.RUB,
            description="Payment 1",
            idempotency_key="idem-key-1",
        )
        dto2 = PaymentCreateDto(
            amount=Decimal("200.00"),
            currency=Currency.USD,
            description="Payment 2",
            idempotency_key="idem-key-2",
        )

        first = await create_payment_usecase.execute(dto1)
        second = await create_payment_usecase.execute(dto2)

        assert first.id != second.id
        assert first.amount != second.amount
        assert first.currency != second.currency

        async with uow:
            p1 = await uow.payments.get_by_id(first.id)
            p2 = await uow.payments.get_by_id(second.id)
            assert p1 is not None
            assert p2 is not None
            assert p1.idempotency_key == "idem-key-1"
            assert p2.idempotency_key == "idem-key-2"

    @pytest.mark.asyncio
    async def test_create_payment_concurrent_same_key(
        self,
        create_payment_usecase: CreatePaymentUseCase,
    ) -> None:
        dto = PaymentCreateDto(
            amount=Decimal("100.00"),
            currency=Currency.RUB,
            description="Concurrent payment",
            idempotency_key="idem-concurrent-key",
        )

        results = await asyncio.gather(*[create_payment_usecase.execute(dto) for _ in range(10)])

        ids = {r.id for r in results}
        assert len(ids) == 1, f"Ожидался 1 уникальный id, получено {len(ids)}: {ids}"

        amounts = {r.amount for r in results}
        assert len(amounts) == 1
        assert Decimal("100.00") in amounts

    @pytest.mark.asyncio
    async def test_create_payment_concurrent_different_keys(
        self,
        create_payment_usecase: CreatePaymentUseCase,
    ) -> None:
        results = await asyncio.gather(
            *[
                create_payment_usecase.execute(
                    PaymentCreateDto(
                        amount=Decimal("100.00"),
                        currency=Currency.RUB,
                        description=f"Concurrent {i}",
                        idempotency_key=f"idem-concurrent-{i}",
                    )
                )
                for i in range(10)
            ]
        )

        ids = {r.id for r in results}
        assert len(ids) == 10, f"Ожидалось 10 уникальных id, получено {len(ids)}"

    @pytest.mark.asyncio
    async def test_create_payment_idempotent_no_duplicate_outbox(
        self,
        create_payment_usecase: CreatePaymentUseCase,
        uow: IUnitOfWork,
    ) -> None:
        dto = PaymentCreateDto(
            amount=Decimal("100.00"),
            currency=Currency.RUB,
            description="Outbox idempotency",
            idempotency_key="idem-outbox-key",
        )

        await create_payment_usecase.execute(dto)
        await create_payment_usecase.execute(dto)

        async with uow:
            events = await uow.outbox.get_pending_events(limit=10)

            assert len(events) == 1, f"Ожидалось 1 outbox-событие, получено {len(events)}"
