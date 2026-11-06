import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.application.usecases import PublishOutboxEventsUseCase
from src.config import settings
from src.domain.exceptions import (
    AppError,
    IdempotencyError,
    InvalidPaymentError,
    ObjectNotFoundError,
)
from src.infrastructure.database.db import engine
from src.infrastructure.database.uow import SQLAlchemyUnitOfWork
from src.infrastructure.rabbitmq.publisher import RabbitMQPublisher
from src.presentation.dependencies import session_factory
from src.presentation.routes import router
from src.presentation.workers.outbox_publisher_worker import OutboxPublisherWorker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Создаёт publisher и Outbox воркер."""
    logger.info("Starting lifespan: RabbitMQPublisher and OutboxPublisherWorker")
    publisher = RabbitMQPublisher(str(settings.rabbitmq_url))
    await publisher.start()

    uow = SQLAlchemyUnitOfWork(session_factory)
    publish_outbox_usecase = PublishOutboxEventsUseCase(
        uow=uow,
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
    logger.info("Lifespan shutdown complete")


async def app_error_handler(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, AppError):
        return JSONResponse(status_code=500, content={"error": "internal error"})
    status_code = 400
    if isinstance(exc, ObjectNotFoundError):
        status_code = 404
    if isinstance(exc, IdempotencyError):
        status_code = 409
    if isinstance(exc, InvalidPaymentError):
        status_code = 400
    return JSONResponse(
        status_code=status_code,
        content={"error": exc.message, "details": exc.details},
    )


async def validation_error_handler(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ValidationError):
        return JSONResponse(status_code=500, content={"error": "internal error"})
    return JSONResponse(
        status_code=422,
        content={"error": "validation error", "details": exc.errors()},
    )


async def health() -> dict[str, str]:
    return {"status": "healthy"}


app = FastAPI(title="Payment Processing API", lifespan=lifespan)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(ValidationError, validation_error_handler)
app.include_router(router)
app.get("/health", status_code=200)(health)
