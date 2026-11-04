from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.interfaces.outbox_repository import IOutboxRepository
from src.domain.interfaces.payment_repository import IPaymentRepository
from src.domain.interfaces.unit_of_work import IUnitOfWork
from src.infrastructure.database.repositories.outbox import SQLAlchemyOutboxRepository
from src.infrastructure.database.repositories.payment import SQLAlchemyPaymentRepository


class SQLAlchemyUnitOfWork(IUnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self.payments: IPaymentRepository
        self.outbox: IOutboxRepository

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self.payments = SQLAlchemyPaymentRepository(self._session)
        self.outbox = SQLAlchemyOutboxRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        tb,
    ) -> None:
        if self._session is None:
            return

        try:
            if exc_type is None:
                await self.commit()
            else:
                await self.rollback()
        finally:
            await self._session.close()
            self._session = None

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
