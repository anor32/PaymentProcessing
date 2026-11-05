from abc import ABC, abstractmethod


class IWebhookSender(ABC):
    @abstractmethod
    async def send(self, url: str, payload: dict) -> None:
        pass
