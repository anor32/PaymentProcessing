from abc import ABC, abstractmethod
from datetime import datetime

from src.domain.entities.payment import Payment
from src.domain.value_objects.payment_objects import PaymentStatus


class IPaymentRepository(ABC):
    @abstractmethod
    async def get_by_id(self, payment_id: str) -> Payment | None:
        pass

    @abstractmethod
    async def create(self, payment: Payment) -> Payment:
        pass

    @abstractmethod
    async def update_status(
        self,
        payment_id: str,
        status: PaymentStatus,
        processed_at: datetime | None = None,
        error_message: str | None = None,
    ) -> None:
        """Updates payment status."""
        pass

    @abstractmethod
    async def update(self, payment: Payment) -> None:
        """Saves updated payment entity."""
        pass
