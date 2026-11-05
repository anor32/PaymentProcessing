import asyncio
import logging

from src.application.dtos.payment_processing_result import (
    PaymentProcessingAction,
    PaymentProcessingResult,
)
from src.domain.entities.payment import Payment
from src.domain.interfaces import IUnitOfWork, IWebhookSender

logger = logging.getLogger(__name__)


class ProcessPaymentUseCase:
    def __init__(
        self,
        webhook_sender: IWebhookSender,
        max_retries: int = 3,
        uow: IUnitOfWork | None = None,
    ) -> None:
        self._webhook_sender = webhook_sender
        self._max_retries = max_retries
        self._uow = uow

    async def execute(
        self,
        payment_id: str,
        retry_count: int = 0,
        uow: IUnitOfWork | None = None,
    ) -> PaymentProcessingResult:
        uow = uow if uow is not None else self._uow
        if uow is None:
            raise ValueError("Unit of Work is required")

        async with uow:
            payment: Payment | None = await uow.payments.get_by_id(payment_id)

            if payment is None:
                logger.warning("Payment %s not found", payment_id)
                return PaymentProcessingResult(
                    action=PaymentProcessingAction.DLQ,
                    target_queue="payments.dlq",
                    retry_count=retry_count,
                    error_message=f"Payment {payment_id} not found",
                )

            logger.info("Processing payment %s...", payment_id)
            await asyncio.sleep(1)

            payment.process()
            logger.info("Payment %s -> %s", payment_id, payment.status.value)

            await uow.payments.update(payment)

            if payment.webhook_url:
                try:
                    payload = payment.to_webhook_payload()

                    await self._webhook_sender.send(
                        url=payment.webhook_url,
                        payload=payload,
                    )
                    logger.info("Webhook sent for payment %s", payment_id)
                except Exception as exc:
                    logger.exception("Webhook failed for payment %s: %s", payment_id, exc)

                    if retry_count >= self._max_retries:
                        return PaymentProcessingResult(
                            action=PaymentProcessingAction.DLQ,
                            target_queue="payments.dlq",
                            retry_count=retry_count,
                            error_message=str(exc),
                        )

                    next_retry = retry_count + 1
                    target_queue = f"payments.retry.{next_retry}"
                    return PaymentProcessingResult(
                        action=PaymentProcessingAction.RETRY,
                        target_queue=target_queue,
                        retry_count=next_retry,
                        error_message=str(exc),
                    )

            await uow.commit()

        return PaymentProcessingResult(
            action=PaymentProcessingAction.SUCCESS,
            retry_count=retry_count,
        )
