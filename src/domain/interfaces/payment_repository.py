from abc import ABC, abstractmethod

from src.domain.entities.payment import Payment


class IPaymentRepository(ABC):
    @abstractmethod
    async def get_by_id(self, payment_id: str) -> Payment | None:
        pass

    @abstractmethod
    async def create(self, payment: Payment) -> Payment:
        pass

    @abstractmethod
    async def update(self, payment: Payment) -> Payment | None:
        pass
