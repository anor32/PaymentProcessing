from unittest.mock import AsyncMock

import pytest

from src.application.usecases.publish_outbox_events import PublishOutboxEventsUseCase
from tests.fakes import FakeUnitOfWork

pytestmark = pytest.mark.asyncio


class TestPublishOutboxEventsUseCase:
    async def test_execute_no_events_does_nothing(
        self,
        publish_outbox_usecase: PublishOutboxEventsUseCase,
        mock_publisher: AsyncMock,
    ) -> None:
        await publish_outbox_usecase.execute()

        mock_publisher.publish.assert_not_awaited()

    async def test_execute_publishes_event_and_marks_published(
        self,
        publish_outbox_usecase: PublishOutboxEventsUseCase,
        mock_publisher: AsyncMock,
        outbox_uow: FakeUnitOfWork,
    ) -> None:
        async with outbox_uow:
            await outbox_uow.outbox.add_event(
                event_type="payment.created",
                payload={"payment_id": "pay-1"},
            )
            await outbox_uow.commit()

        await publish_outbox_usecase.execute()

        mock_publisher.publish.assert_awaited_once()
        call_args = mock_publisher.publish.await_args
        assert call_args.kwargs["queue_name"] == "payments.new"
        assert call_args.kwargs["message"]["event_type"] == "payment.created"
        assert call_args.kwargs["message"]["payload"]["payment_id"] == "pay-1"

    async def test_execute_publish_failure_marks_failed(
        self,
        publish_outbox_usecase: PublishOutboxEventsUseCase,
        mock_publisher: AsyncMock,
        outbox_uow: FakeUnitOfWork,
    ) -> None:
        mock_publisher.publish.side_effect = Exception("Broker down")

        async with outbox_uow:
            await outbox_uow.outbox.add_event(
                event_type="payment.created",
                payload={},
            )
            await outbox_uow.commit()

        await publish_outbox_usecase.execute()

        events = await outbox_uow.outbox.get_pending_events(limit=10)
        failed_events = [e for e in events if e.get("status") == "failed"]
        assert len(failed_events) >= 1

    async def test_multiple_cycles_use_separate_uow_instances(
        self,
        mock_publisher: AsyncMock,
    ) -> None:
        for _ in range(3):
            usecase = PublishOutboxEventsUseCase(
                uow=FakeUnitOfWork(),
                publisher=mock_publisher,
                queue_name="payments.new",
                batch_size=10,
            )
            await usecase.execute()
