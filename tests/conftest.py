import asyncio
import os
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.application.dtos.payment_create_dto import PaymentCreateDto
from src.application.usecases.create_payment import CreatePaymentUseCase
from src.application.usecases.get_payment import GetPaymentUseCase
from src.application.usecases.process_payment import ProcessPaymentUseCase
from src.application.usecases.publish_outbox_events import PublishOutboxEventsUseCase
from src.config import Settings
from src.domain.entities.payment import Payment
from src.domain.interfaces.payment_repository import IPaymentRepository
from src.domain.interfaces.webhook_sender import IWebhookSender
from src.presentation.dependencies import get_create_payment_usecase, get_get_payment_usecase
from src.presentation.emulation_service.config import ConsumerConfig
from src.presentation.main import app
from tests.fakes import FakeUnitOfWork
from tests.test_data import (
    PAYMENT_1_DATA,
    PAYMENT_2_DATA,
    PAYMENT_CREATE_DTO_DATA,
    PAYMENT_ENTITY_DATA,
    make_payment,
    make_payment_1,
    make_payment_2,
)


@pytest.fixture(scope="session")
def event_loop() -> Any:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def settings() -> Settings:
    return Settings(
        POSTGRES_CONNECTION_STRING=os.getenv(
            "POSTGRES_CONNECTION_STRING",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/payment_processing_test",
        ),
        API_KEY=os.getenv("API_KEY", "test-api-key"),
    )


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def payment_repo(uow: FakeUnitOfWork) -> IPaymentRepository:
    return uow.payments


@pytest.fixture
def create_payment_usecase(uow: FakeUnitOfWork) -> CreatePaymentUseCase:
    return CreatePaymentUseCase(uow)


@pytest.fixture
def get_payment_usecase(uow: FakeUnitOfWork) -> GetPaymentUseCase:
    return GetPaymentUseCase(uow)


@pytest.fixture
def webhook_sender() -> AsyncMock:
    return AsyncMock(spec=IWebhookSender)


@pytest.fixture
def process_payment_usecase(webhook_sender: AsyncMock) -> ProcessPaymentUseCase:
    return ProcessPaymentUseCase(webhook_sender)


@pytest.fixture
def payment_entity() -> Payment:
    return make_payment(**PAYMENT_ENTITY_DATA)


@pytest.fixture
async def saved_payment(uow: FakeUnitOfWork, payment_entity: Payment) -> Payment:
    async with uow:
        await uow.payments.create(payment_entity)
    return payment_entity


@pytest.fixture
def payment_create_dto() -> PaymentCreateDto:
    return PaymentCreateDto(**PAYMENT_CREATE_DTO_DATA)


@pytest.fixture
def mock_publisher() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def outbox_uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def consumer_config() -> Any:
    return ConsumerConfig()


@pytest.fixture
def publish_outbox_usecase(
    outbox_uow: FakeUnitOfWork,
    mock_publisher: AsyncMock,
) -> PublishOutboxEventsUseCase:
    return PublishOutboxEventsUseCase(
        uow=outbox_uow,
        publisher=mock_publisher,
        queue_name="payments.new",
        batch_size=10,
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def mock_create_usecase() -> AsyncMock:
    mock = AsyncMock(spec=CreatePaymentUseCase)
    mock_payment = make_payment_1(**PAYMENT_1_DATA)
    mock.execute.return_value = mock_payment
    app.dependency_overrides[get_create_payment_usecase] = lambda: mock
    yield mock
    app.dependency_overrides.clear()


@pytest.fixture
def mock_get_usecase() -> AsyncMock:
    mock = AsyncMock(spec=GetPaymentUseCase)
    mock_payment = make_payment_2(**{**PAYMENT_2_DATA, "id": "pay-1"})
    mock.execute.return_value = mock_payment
    app.dependency_overrides[get_get_payment_usecase] = lambda: mock
    yield mock
    app.dependency_overrides.clear()
