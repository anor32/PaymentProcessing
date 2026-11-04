from abc import ABC, abstractmethod
from typing import Any


class IOutboxRepository(ABC):
    @abstractmethod
    async def add_event(self, event_type: str, payload: dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def get_pending_events(self, limit: int) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def mark_published(self, event_id: str) -> None:
        pass

    @abstractmethod
    async def mark_failed(self, event_id: str, error_message: str | None = None) -> None:
        pass
