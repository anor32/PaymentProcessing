import logging

from src.domain.interfaces import IMessagePublisher, IUnitOfWork
from src.domain.interfaces.outbox_repository import IOutboxRepository

logger = logging.getLogger(__name__)


class PublishOutboxEventsUseCase:
    def __init__(
        self,
        uow: IUnitOfWork,
        publisher: IMessagePublisher,
        queue_name: str = "payments.new",
        batch_size: int = 10,
    ) -> None:
        self._uow = uow
        self._publisher = publisher
        self._queue_name = queue_name
        self._batch_size = batch_size

    async def execute(self) -> None:
        async with self._uow as uow:
            outbox_repo: IOutboxRepository = uow.outbox
            events = await outbox_repo.get_pending_events(limit=self._batch_size)

            for event in events:
                if event.get("id") is None:
                    continue
                try:
                    await self._publisher.publish(
                        message={
                            "event_type": str(event["event_type"]),
                            "payload": event["payload"],
                        },
                        queue_name=self._queue_name,
                    )
                    await outbox_repo.mark_published(str(event["id"]))
                    logger.info("Event %s published to %s", event["id"], self._queue_name)
                except Exception as exc:
                    logger.exception("Failed to publish event %s: %s", event["id"], exc)
                    await outbox_repo.mark_failed(str(event["id"]), error_message=str(exc))

            await uow.commit()
