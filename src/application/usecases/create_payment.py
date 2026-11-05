from src.application.dtos.payment_create_dto import PaymentCreateDto
from src.domain.entities.payment import Payment
from src.domain.interfaces.unit_of_work import IUnitOfWork


class CreatePaymentUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, create_dto: PaymentCreateDto) -> Payment:
        payment = create_dto.to_entity()

        async with self._uow:
            created = await self._uow.payments.create(payment)
            if created.id == payment.id:
                await self._uow.outbox.add_event(
                    event_type="payment.created",
                    payload=created.to_payload(),
                )

        return created
