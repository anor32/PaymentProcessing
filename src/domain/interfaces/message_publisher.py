from abc import ABC, abstractmethod
from typing import Any


class IMessagePublisher(ABC):
    @abstractmethod
    async def publish(self, message: dict[str, Any], queue_name: str) -> None:
        pass
