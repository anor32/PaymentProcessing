import asyncio
import logging
from collections.abc import Callable
from typing import Any, cast

from faststream.rabbit import RabbitBroker, RabbitQueue

from src.application.dtos.payment_processing_result import PaymentProcessingAction
from src.application.usecases.process_payment import ProcessPaymentUseCase
from src.domain.interfaces import IUnitOfWork
from src.presentation.emulation_service.config import ConsumerConfig

logger = logging.getLogger(__name__)


class RabbitConsumer:
    def __init__(
        self,
        broker: RabbitBroker,
        create_uow: Callable[[], IUnitOfWork],
        usecase: ProcessPaymentUseCase,
        config: ConsumerConfig | None = None,
    ) -> None:
        self._broker = broker
        self._create_uow = create_uow
        self._usecase = usecase
        self._config = config or ConsumerConfig()
        self._queue_name = self._config.queue_name

    def _extract_retry_count(self, message) -> int:
        try:
            headers = getattr(message, "headers", None) or {}
            x_death = headers.get("x-death", [])
            if not isinstance(x_death, list):
                return 0
            count = 0
            for death in x_death:
                if death.get("queue") == self._queue_name and death.get("reason") == "rejected":
                    count += 1
            return count
        except Exception:
            logger.exception("Failed to parse x-death headers, falling back to 0")
            return 0

    async def _send_dlq(self, body: dict, error_msg: str) -> None:
        message_body = {**body, "error": error_msg}
        await self._broker.publish(message=message_body, queue=self._config.dlq_name)
        logger.info("Message sent to DLQ %s", self._config.dlq_name)

    async def _send_retry(
        self,
        body: dict,
        target_queue: str,
        retry_count: int,
        error_msg: str,
    ) -> None:
        message_body = {
            **body,
            "retry_count": retry_count,
            "error": error_msg,
        }
        await self._broker.publish(message=message_body, queue=target_queue)
        logger.info("Published to retry queue %s", target_queue)

    async def _retry(self, body: dict, error_msg: str, retry_count: int) -> int:
        next_retry = retry_count + 1
        delay_seconds = self._config.retry_delay_seconds(next_retry)
        target_queue = (
            self._config.retry_queues[next_retry - 1]
            if next_retry <= len(self._config.retry_queues)
            else f"payments.retry.{next_retry}"
        )

        await self._send_retry(
            body=body,
            target_queue=target_queue,
            retry_count=next_retry,
            error_msg=error_msg,
        )

        logger.info(
            "Retrying payment %s -> queue=%s attempt=%d backoff=%ss error=%s",
            body.get("payment_id"),
            target_queue,
            next_retry,
            delay_seconds,
            error_msg,
        )
        return next_retry

    def _transform_message(self, body: dict) -> dict:
        message_body: dict = dict(body or {})
        payload = message_body.get("payload")
        if isinstance(payload, dict):
            message_body = {
                **payload,
                **{k: v for k, v in message_body.items() if k not in ("payload", "event_type")},
            }
        return message_body

    async def consume(self, body: dict, message) -> None:
        message_body = self._transform_message(body)
        retry_count = self._extract_retry_count(message)
        payment_id = message_body.get("payment_id")
        if not payment_id:
            logger.error("Message without payment_id: %s", body)
            return

        logger.info("Received message for payment %s (retry_count=%d)", payment_id, retry_count)

        async with self._create_uow() as uow:
            result = await self._usecase.execute(
                payment_id=payment_id,
                retry_count=retry_count,
                uow=uow,
            )

            if result.action == PaymentProcessingAction.SUCCESS:
                logger.info("Payment %s processed successfully", payment_id)
            elif result.action == PaymentProcessingAction.RETRY:
                logger.info(
                    "Payment %s retry -> %s (attempt %d, error=%s)",
                    payment_id,
                    result.target_queue,
                    result.retry_count,
                    result.error_message or "unknown error",
                )
                await self._retry(
                    body=message_body,
                    error_msg=result.error_message or "unknown error",
                    retry_count=retry_count,
                )
            elif result.action == PaymentProcessingAction.DLQ:
                logger.error(
                    "Payment %s -> DLQ (%s)",
                    payment_id,
                    result.error_message or "unknown error",
                )
                await self._send_dlq(message_body, result.error_message or "unknown error")

    async def run(self) -> None:
        queue = RabbitQueue(
            self._queue_name,
            durable=True,
            arguments=cast(Any, self._config.main_queue_arguments),
        )

        async def handler(body: dict, message) -> None:
            await self.consume(body, message)

        self._broker.subscriber(queue)(handler)

        await self._broker.start()

        logger.info("Consumer started, waiting for messages on %s...", self._queue_name)

        stop_event = asyncio.Event()
        try:
            await stop_event.wait()
        except asyncio.CancelledError:
            pass
        finally:
            await self._broker.stop()
