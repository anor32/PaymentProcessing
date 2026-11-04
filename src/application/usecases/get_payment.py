from domain.entities.payment import Payment
from domain.exceptions import ObjectNotFoundError
from src.domain.interfaces.unit_of_work import IUnitOfWork


class GetPaymentUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, payment_id: str) -> Payment:
        async with self._uow:
            payment = await self._uow.payments.get_by_id(payment_id)

            if payment is None:
                raise ObjectNotFoundError(f"Payment with id '{payment_id}' not found")

            return payment
