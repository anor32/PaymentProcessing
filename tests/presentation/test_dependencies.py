import inspect
from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.interfaces.unit_of_work import IUnitOfWork
from src.infrastructure.database.uow import SQLAlchemyUnitOfWork
from src.presentation.dependencies import (
    CreatePaymentDep,
    GetPaymentDep,
    SessionDep,
    UowDep,
    get_session,
    get_uow,
)


class TestDependencies:
    def test_get_session_is_async_generator(self) -> None:
        assert inspect.isasyncgenfunction(get_session)

    def test_get_uow_returns_iunitofwork(self) -> None:
        session = AsyncMock(spec=AsyncSession)
        result = get_uow(session)

        assert isinstance(result, SQLAlchemyUnitOfWork)
        assert isinstance(result, IUnitOfWork)

    def test_create_payment_dep_type(self) -> None:
        assert CreatePaymentDep is not None

    def test_get_payment_dep_type(self) -> None:
        assert GetPaymentDep is not None

    def test_session_dep_type(self) -> None:
        assert SessionDep is not None

    def test_uow_dep_type(self) -> None:
        assert UowDep is not None
