from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.application.usecases import PublishOutboxEventsUseCase
from src.config import settings
from src.infrastructure.database.db import engine
from src.infrastructure.rabbitmq.publisher import RabbitMQPublisher
from src.presentation.dependencies import session_factory
from src.presentation.routes import router
from src.presentation.workers.outbox_publisher_worker import OutboxPublisherWorker


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Создаёт publisher и Outbox воркер."""
    publisher = RabbitMQPublisher(settings.rabbitmq_url)
    await publisher.start()

    publish_outbox_usecase = PublishOutboxEventsUseCase(
        session_factory=session_factory,
        publisher=publisher,
        queue_name="payments.new",
        batch_size=10,
    )
    worker = OutboxPublisherWorker(usecase=publish_outbox_usecase, interval=1.0)
    worker.start()

    yield

    worker.stop()
    await worker.wait()

    await publisher.stop()
    await engine.dispose()


app = FastAPI(title="Payment Processing API", lifespan=lifespan)
app.include_router(router)
