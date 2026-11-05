from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from src.application.dtos.payment_processing_result import (
    PaymentProcessingAction,
    PaymentProcessingResult,
)
from src.application.usecases.process_payment import ProcessPaymentUseCase
from src.domain.entities.payment import Payment
from src.domain.interfaces.unit_of_work import IUnitOfWork
from src.domain.value_objects.payment_objects import Currency, PaymentStatus

pytestmark = pytest.mark.asyncio


class TestProcessPaymentUseCase:
    async def test_process_payment_marks_succeeded(
        self,
        uow: IUnitOfWork,
        saved_payment: Payment,
        webhook_sender: AsyncMock,
        process_payment_usecase: ProcessPaymentUseCase,
    ) -> None:
        with patch("src.domain.entities.payment.random.random", return_value=0.0):
            result = await process_payment_usecase.execute(saved_payment.id, uow=uow)

        assert result.action == PaymentProcessingAction.SUCCESS

        async with uow:
            updated = await uow.payments.get_by_id(saved_payment.id)
            assert updated is not None
            assert updated.status == PaymentStatus.SUCCEEDED
            assert updated.processed_at is not None

        webhook_sender.send.assert_awaited_once()
        call_args = webhook_sender.send.await_args
        assert call_args.kwargs["url"] == saved_payment.webhook_url
        assert call_args.kwargs["payload"]["payment_id"] == saved_payment.id
        assert call_args.kwargs["payload"]["status"] == "succeeded"

    async def test_process_payment_not_found_returns_dlq(
        self,
        uow: IUnitOfWork,
        webhook_sender: AsyncMock,
        process_payment_usecase: ProcessPaymentUseCase,
    ) -> None:
        result = await process_payment_usecase.execute("non-existent-id", uow=uow)

        assert isinstance(result, PaymentProcessingResult)
        assert result.action == PaymentProcessingAction.DLQ
        assert result.target_queue == "payments.dlq"
        assert "not found" in result.error_message

        webhook_sender.send.assert_not_awaited()

    async def test_process_payment_webhook_failure_returns_retry(
        self,
        uow: IUnitOfWork,
        saved_payment: Payment,
        webhook_sender: AsyncMock,
    ) -> None:
        webhook_sender.send.side_effect = Exception("Broker down")
        usecase = ProcessPaymentUseCase(webhook_sender, max_retries=3)

        result = await usecase.execute(saved_payment.id, retry_count=0, uow=uow)

        assert result.action == PaymentProcessingAction.RETRY
        assert result.target_queue == "payments.retry.1"
        assert result.retry_count == 1
        assert "Broker down" in result.error_message

    async def test_process_payment_webhook_max_retries_returns_dlq(
        self,
        uow: IUnitOfWork,
        saved_payment: Payment,
        webhook_sender: AsyncMock,
    ) -> None:
        webhook_sender.send.side_effect = Exception("Broker down")
        usecase = ProcessPaymentUseCase(webhook_sender, max_retries=3)

        result = await usecase.execute(saved_payment.id, retry_count=3, uow=uow)

        assert result.action == PaymentProcessingAction.DLQ
        assert result.target_queue == "payments.dlq"
        assert result.retry_count == 3

    async def test_process_payment_no_webhook_url_still_succeeds(
        self,
        uow: IUnitOfWork,
        payment_entity: Payment,
        webhook_sender: AsyncMock,
        process_payment_usecase: ProcessPaymentUseCase,
    ) -> None:
        payment_no_webhook = Payment(
            id="pay-no-webhook",
            amount=Decimal("100.00"),
            currency=Currency.RUB,
            description="No webhook",
            status=PaymentStatus.PENDING,
            idempotency_key="idem-no-webhook",
            webhook_url=None,
        )
        async with uow:
            await uow.payments.create(payment_no_webhook)

        result = await process_payment_usecase.execute(payment_no_webhook.id, uow=uow)

        assert result.action == PaymentProcessingAction.SUCCESS
        webhook_sender.send.assert_not_awaited()

    async def test_process_payment_marks_failed(
        self,
        uow: IUnitOfWork,
        saved_payment: Payment,
        webhook_sender: AsyncMock,
        process_payment_usecase: ProcessPaymentUseCase,
    ) -> None:
        with patch("src.domain.entities.payment.random.random", return_value=1.0):
            result = await process_payment_usecase.execute(saved_payment.id, uow=uow)

        assert result.action == PaymentProcessingAction.SUCCESS

        async with uow:
            updated = await uow.payments.get_by_id(saved_payment.id)
            assert updated is not None
            assert updated.status == PaymentStatus.FAILED
            assert updated.processed_at is not None

        webhook_sender.send.assert_awaited_once()
        call_args = webhook_sender.send.await_args
        assert call_args.kwargs["url"] == saved_payment.webhook_url
        assert call_args.kwargs["payload"]["status"] == "failed"
