import inspect

from src.domain.interfaces.unit_of_work import IUnitOfWork
from src.infrastructure.database.uow import SQLAlchemyUnitOfWork


class TestDependencies:
    def test_get_session_is_async_generator(self) -> None:
        from src.presentation.dependencies import get_session

        assert inspect.isasyncgenfunction(get_session)

    def test_get_uow_returns_iunitofwork(self) -> None:
        from src.presentation.dependencies import get_uow

        result = get_uow()

        assert isinstance(result, SQLAlchemyUnitOfWork)
        assert isinstance(result, IUnitOfWork)

    def test_create_payment_dep_type(self) -> None:
        from src.presentation.dependencies import CreatePaymentDep

        assert CreatePaymentDep is not None

    def test_get_payment_dep_type(self) -> None:
        from src.presentation.dependencies import GetPaymentDep

        assert GetPaymentDep is not None

    def test_session_dep_type(self) -> None:
        from src.presentation.dependencies import SessionDep

        assert SessionDep is not None

    def test_uow_dep_type(self) -> None:
        from src.presentation.dependencies import UowDep

        assert UowDep is not None
