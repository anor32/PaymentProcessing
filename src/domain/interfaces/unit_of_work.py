from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from src.domain.interfaces.outbox_repository import IOutboxRepository
from src.domain.interfaces.payment_repository import IPaymentRepository


class IUnitOfWork(ABC):
    payments: IPaymentRepository
    outbox: IOutboxRepository

    @abstractmethod
    async def __aenter__(self) -> Self:
        pass

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        pass

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass
