from abc import ABC, abstractmethod
from typing import Any


class IMessagePublisher(ABC):
    """Interface for publishing messages to a message broker."""

    @abstractmethod
    async def publish(self, message: dict[str, Any], queue_name: str) -> None:
        """Publishes a message to the specified queue."""
        pass
