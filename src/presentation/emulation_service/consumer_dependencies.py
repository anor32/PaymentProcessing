"""Dependencies for the Consumer (emulation gateway) service.

Provides FastAPI-style dependency functions that inject into RabbitConsumer:
- ConsumerConfig
- AsyncSession / IUnitOfWork
- ProcessPaymentUseCase
- RabbitBroker
- RabbitConsumer (assembled from injected deps via RabbitConsumerDep)

The Consumer receives all collaborators via Consumer Deps (constructor injection),
it does NOT create them on its own. A new Unit of Work is created for every
message via the injected create_uow factory.
"""

from collections.abc import AsyncGenerator, Callable
from typing import Annotated

from fastapi import Depends
from faststream.rabbit import RabbitBroker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.usecases.process_payment import ProcessPaymentUseCase
from src.config import settings
from src.domain.interfaces import IUnitOfWork
from src.infrastructure.database.db import engine
from src.infrastructure.database.uow import SQLAlchemyUnitOfWork
from src.infrastructure.webhook.http_webhook_sender import HttpWebhookSender
from src.presentation.emulation_service.config import ConsumerConfig
from src.presentation.emulation_service.consumer import RabbitConsumer

session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_uow(session: SessionDep) -> IUnitOfWork:
    return SQLAlchemyUnitOfWork(session)


UowDep = Annotated[IUnitOfWork, Depends(get_uow)]


def get_consumer_config() -> ConsumerConfig:
    """Provides ConsumerConfig (broker topology, retries, backoff)."""
    return ConsumerConfig()


ConsumerConfigDep = Annotated[ConsumerConfig, Depends(get_consumer_config)]


def create_uow_consumer(session_factory: async_sessionmaker) -> Callable[[], IUnitOfWork]:
    """Factory that creates a new Unit of Work for every consumer message.

    Returns a callable that the RabbitConsumer invokes for each incoming
    message so a fresh DB session / UoW is used per message.
    """

    def _create_uow() -> IUnitOfWork:
        return SQLAlchemyUnitOfWork(session_factory)

    return _create_uow


def get_process_payment_usecase(uow: UowDep, config: ConsumerConfigDep) -> ProcessPaymentUseCase:
    """Builds ProcessPaymentUseCase from injected Unit of Work and ConsumerConfig."""
    return ProcessPaymentUseCase(
        uow=uow,
        webhook_sender=HttpWebhookSender(),
        max_retries=config.max_retries,
    )


ProcessPaymentUseCaseDep = Annotated[ProcessPaymentUseCase, Depends(get_process_payment_usecase)]


def get_rabbit_broker() -> RabbitBroker:
    """Creates a RabbitBroker instance for connecting to RabbitMQ."""
    return RabbitBroker(settings.rabbitmq_url)


RabbitBrokerDep = Annotated[RabbitBroker, Depends(get_rabbit_broker)]


def get_rabbit_consumer(
    broker: RabbitBrokerDep,
    usecase: ProcessPaymentUseCaseDep,
    config: ConsumerConfigDep,
) -> RabbitConsumer:
    """Creates a RabbitConsumer with configured broker, create_uow, usecase, and config.

    All collaborators are injected via Consumer Deps, the consumer itself
    receives them through constructor injection.
    """
    return RabbitConsumer(
        broker=broker,
        create_uow=create_uow_consumer(session_factory),
        usecase=usecase,
        config=config,
    )


RabbitConsumerDep = Annotated[RabbitConsumer, Depends(get_rabbit_consumer)]
