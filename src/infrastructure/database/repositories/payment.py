from dataclasses import fields

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.payment import Payment
from src.domain.interfaces.payment_repository import IPaymentRepository
from src.infrastructure.database.models import Payment as PaymentModel


class SQLAlchemyPaymentRepository(IPaymentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _model_to_entity(self, model: PaymentModel) -> Payment:
        """ORM-модель -> доменная сущность."""
        return Payment(
            id=model.id,
            amount=model.amount,
            currency=model.currency,
            description=model.description,
            metadata=model.metadata_json or {},
            status=model.status,
            idempotency_key=model.idempotency_key,
            webhook_url=model.webhook_url,
            created_at=model.created_at,
            processed_at=model.processed_at,
            error_message=model.error_message,
        )

    async def get_by_id(self, payment_id: str) -> Payment | None:
        model = await self._session.get(PaymentModel, payment_id)
        if model is None:
            return None
        return self._model_to_entity(model)

    async def create(self, payment: Payment) -> Payment:
        model = PaymentModel(
            id=payment.id,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            metadata_json=payment.metadata,
            status=payment.status,
            idempotency_key=payment.idempotency_key,
            webhook_url=payment.webhook_url,
            processed_at=payment.processed_at,
            error_message=payment.error_message,
        )

        self._session.add(model)
        await self._session.flush()
        return self._model_to_entity(model)

    async def update(self, payment: Payment) -> Payment | None:
        model = await self._session.get(PaymentModel, payment.id)
        if model is None:
            return None

        for field in fields(payment):
            name = field.name
            if name == "id":
                continue
            value = getattr(payment, name)
            if value is None:
                continue
            column_name = "metadata_json" if name == "metadata" else name
            setattr(model, column_name, value)

        await self._session.flush()
        return self._model_to_entity(model)
