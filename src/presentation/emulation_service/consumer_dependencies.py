from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from faststream.rabbit import RabbitBroker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.usecases.process_payment import ProcessPaymentUseCase
from src.config import settings
from src.domain.interfaces import IUnitOfWork
from src.infrastructure.database.uow import SQLAlchemyUnitOfWork
from src.infrastructure.webhook.http_webhook_sender import HttpWebhookSender
from src.presentation.dependencies import UowDep, session_factory
from src.presentation.emulation_service.config import ConsumerConfig
from src.presentation.emulation_service.consumer import RabbitConsumer


def get_consumer_config() -> ConsumerConfig:
    return ConsumerConfig(rabbitmq_url=str(settings.rabbitmq_url))


ConsumerConfigDep = Annotated[ConsumerConfig, Depends(get_consumer_config)]


def get_rabbit_broker() -> RabbitBroker:
    return RabbitBroker(str(settings.rabbitmq_url))


RabbitBrokerDep = Annotated[RabbitBroker, Depends(get_rabbit_broker)]


def create_uow_consumer(factory: async_sessionmaker[AsyncSession]) -> Callable[[], IUnitOfWork]:
    def _create_uow() -> IUnitOfWork:
        return SQLAlchemyUnitOfWork(factory)

    return _create_uow


def get_process_payment_usecase(uow: UowDep, config: ConsumerConfigDep) -> ProcessPaymentUseCase:
    return ProcessPaymentUseCase(
        uow=uow,
        webhook_sender=HttpWebhookSender(),
        max_retries=config.max_retries,
    )


ProcessPaymentUseCaseDep = Annotated[ProcessPaymentUseCase, Depends(get_process_payment_usecase)]


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
