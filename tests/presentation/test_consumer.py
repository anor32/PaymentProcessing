from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.dtos.payment_processing_result import (
    PaymentProcessingAction,
    PaymentProcessingResult,
)
from src.application.usecases.process_payment import ProcessPaymentUseCase
from src.presentation.emulation_service.consumer import RabbitConsumer
from tests.fakes import FakeUnitOfWork

pytestmark = pytest.mark.asyncio


def make_consumer(consumer_config: Any) -> RabbitConsumer:
    broker = MagicMock()
    broker.publish = AsyncMock()
    return RabbitConsumer(
        broker=broker,
        create_uow=lambda: FakeUnitOfWork(),
        usecase=AsyncMock(spec=ProcessPaymentUseCase),
        config=consumer_config,
    )


class TestRabbitConsumerRetry:
    async def test_retry_schedules_next_attempt(self, consumer_config: Any) -> None:
        consumer = make_consumer(consumer_config)

        next_retry = await consumer._retry(
            body={"payment_id": "pay-1", "amount": "100.50"},
            error_msg="Broker down",
            retry_count=0,
        )

        assert next_retry == 1
        consumer._broker.publish.assert_awaited_once()
        kwargs = consumer._broker.publish.await_args.kwargs
        assert kwargs["queue"] == "payments.retry.1"
        assert kwargs["message"]["payment_id"] == "pay-1"
        assert kwargs["message"]["retry_count"] == 1
        assert kwargs["message"]["error"] == "Broker down"

    async def test_retry_backoff_is_exponential(self, consumer_config: Any) -> None:
        consumer = make_consumer(consumer_config)

        assert consumer._config.retry_delay_seconds(1) == pytest.approx(1.0)
        assert consumer._config.retry_delay_seconds(2) == pytest.approx(2.0)
        assert consumer._config.retry_delay_seconds(3) == pytest.approx(4.0)
        assert consumer._config.retry_delay_seconds(4) == pytest.approx(8.0)
        assert consumer._config.retry_delay_seconds(5) == pytest.approx(16.0)

        assert consumer._config.retry_delay_seconds(20) == pytest.approx(30.0)


class TestRabbitConsumerConsume:
    async def test_success_message_is_not_resent(self, consumer_config: Any) -> None:
        consumer = make_consumer(consumer_config)
        consumer._usecase.execute = AsyncMock(
            return_value=PaymentProcessingResult(
                action=PaymentProcessingAction.SUCCESS, retry_count=0
            ),
        )

        await consumer.consume({"payment_id": "pay-1"}, MagicMock())

        consumer._usecase.execute.assert_awaited_once()
        consumer._broker.publish.assert_not_awaited()

    async def test_retryable_error_routes_to_retry_queue(self, consumer_config: Any) -> None:
        consumer = make_consumer(consumer_config)
        consumer._usecase.execute = AsyncMock(
            return_value=PaymentProcessingResult(
                action=PaymentProcessingAction.RETRY,
                target_queue="payments.retry.1",
                retry_count=1,
                error_message="Broker down",
            ),
        )

        await consumer.consume({"payment_id": "pay-1"}, MagicMock())

        consumer._broker.publish.assert_awaited_once()
        kwargs = consumer._broker.publish.await_args.kwargs
        assert kwargs["queue"] == "payments.retry.1"
        assert kwargs["message"]["retry_count"] == 1
        assert kwargs["message"]["error"] == "Broker down"

    async def test_permanent_error_routes_to_dlq(self, consumer_config: Any) -> None:
        consumer = make_consumer(consumer_config)
        consumer._usecase.execute = AsyncMock(
            return_value=PaymentProcessingResult(
                action=PaymentProcessingAction.DLQ,
                target_queue="payments.dlq",
                retry_count=3,
                error_message="Payment pay-1 not found",
            ),
        )

        await consumer.consume({"payment_id": "pay-1"}, MagicMock())

        consumer._broker.publish.assert_awaited_once()
        kwargs = consumer._broker.publish.await_args.kwargs
        assert kwargs["queue"] == "payments.dlq"
        assert kwargs["message"]["error"] == "Payment pay-1 not found"

    async def test_message_is_transformed_before_processing(self, consumer_config: Any) -> None:
        consumer = make_consumer(consumer_config)
        consumer._usecase.execute = AsyncMock(
            return_value=PaymentProcessingResult(
                action=PaymentProcessingAction.SUCCESS, retry_count=0
            ),
        )

        await consumer.consume(
            {
                "event_type": "payment.succeeded",
                "payload": {"payment_id": "pay-1", "status": "succeeded"},
            },
            MagicMock(),
        )

        consumer._usecase.execute.assert_awaited_once()
        assert consumer._usecase.execute.await_args.kwargs["payment_id"] == "pay-1"
