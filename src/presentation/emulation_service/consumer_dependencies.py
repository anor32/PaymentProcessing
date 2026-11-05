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


def get_uow(session: SessionDep) -> IUnitOfWork:
    return SQLAlchemyUnitOfWork(session)


def get_consumer_config() -> ConsumerConfig:
    return ConsumerConfig()


def create_uow_consumer(session_factory: async_sessionmaker) -> Callable[[], IUnitOfWork]:
    def _create_uow() -> IUnitOfWork:
        return SQLAlchemyUnitOfWork(session_factory)

    return _create_uow


def get_process_payment_usecase(uow: UowDep, config: ConsumerConfigDep) -> ProcessPaymentUseCase:
    return ProcessPaymentUseCase(
        uow=uow,
        webhook_sender=HttpWebhookSender(),
        max_retries=config.max_retries,
    )


def get_rabbit_broker() -> RabbitBroker:
    return RabbitBroker(settings.rabbitmq_url)


RabbitBrokerDep = Annotated[RabbitBroker, Depends(get_rabbit_broker)]


def get_rabbit_consumer(
        broker: RabbitBrokerDep,
        usecase: ProcessPaymentUseCaseDep,
        config: ConsumerConfigDep,
) -> RabbitConsumer:
    return RabbitConsumer(
        broker=broker,
        create_uow=create_uow_consumer(session_factory),
        usecase=usecase,
        config=config,
    )


RabbitConsumerDep = Annotated[RabbitConsumer, Depends(get_rabbit_consumer)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]
UowDep = Annotated[IUnitOfWork, Depends(get_uow)]
ConsumerConfigDep = Annotated[ConsumerConfig, Depends(get_consumer_config)]
ProcessPaymentUseCaseDep = Annotated[ProcessPaymentUseCase, Depends(get_process_payment_usecase)]
