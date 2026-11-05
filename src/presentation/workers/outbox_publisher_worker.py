import asyncio
import logging

from src.application.usecases.publish_outbox_events import PublishOutboxEventsUseCase

logger = logging.getLogger(__name__)


class OutboxPublisherWorker:
    def __init__(
        self,
        usecase: PublishOutboxEventsUseCase,
        interval: float = 1.0,
    ) -> None:
        self._usecase = usecase
        self._interval = interval
        self._stop = asyncio.Event()
        self._task: asyncio.Task | None = None

    async def _run(self) -> None:
        logger.info("OutboxPublisherWorker started (interval=%ss)", self._interval)
        while not self._stop.is_set():
            await self._usecase.execute()
            await asyncio.sleep(self._interval)
        logger.info("OutboxPublisherWorker stopped")

    def stop(self) -> None:
        self._stop.set()

    async def wait(self) -> None:
        if self._task is not None:
            await self._task

    def start(self) -> asyncio.Task:
        self._task = asyncio.create_task(self._run())
        return self._task
