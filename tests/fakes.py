from collections.abc import Sequence
from typing import Any, Self

from src.domain.entities.payment import Payment
from src.domain.interfaces.outbox_repository import IOutboxRepository
from src.domain.interfaces.payment_repository import IPaymentRepository
from src.domain.interfaces.unit_of_work import IUnitOfWork


class FakePaymentRepository(IPaymentRepository):
    def __init__(self) -> None:
        self._payments: dict[str, Payment] = {}
        self._idempotency_index: dict[str, str] = {}

    async def get_by_id(self, payment_id: str) -> Payment | None:
        return self._payments.get(payment_id)

    async def create(self, payment: Payment) -> Payment:
        if (
            payment.idempotency_key is not None
            and payment.idempotency_key in self._idempotency_index
        ):
            existing_id = self._idempotency_index[payment.idempotency_key]
            return self._payments[existing_id]

        self._payments[payment.id] = payment
        if payment.idempotency_key is not None:
            self._idempotency_index[payment.idempotency_key] = payment.id
        return payment

    async def update(self, payment: Payment) -> Payment | None:
        if payment.id not in self._payments:
            return None
        self._payments[payment.id] = payment
        return payment


class FakeOutboxRepository(IOutboxRepository):
    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []
        self._counter = 0

    async def add_event(self, event_type: str, payload: dict[str, Any]) -> None:
        self._counter += 1
        self._events.append(
            {"id": str(self._counter), "event_type": event_type, "payload": payload}
        )

    async def get_pending_events(self, limit: int) -> Sequence[dict[str, Any]]:
        return [e for e in self._events if e.get("status") != "published"][:limit]

    async def mark_published(self, event_id: str) -> None:
        for event in self._events:
            if event["id"] == event_id:
                event["status"] = "published"
                break

    async def mark_failed(self, event_id: str, error_message: str | None = None) -> None:
        for event in self._events:
            if event["id"] == event_id:
                event["status"] = "failed"
                event["error_message"] = error_message
                break


class FakeUnitOfWork(IUnitOfWork):
    def __init__(self) -> None:
        self.payments = FakePaymentRepository()
        self.outbox = FakeOutboxRepository()
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: Any,
    ) -> None:
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True
