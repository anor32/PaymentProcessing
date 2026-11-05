from abc import ABC, abstractmethod


class IWebhookSender(ABC):
    """Interface for sending webhook notifications."""

    @abstractmethod
    async def send(self, url: str, payload: dict) -> None:
        """Sends a POST request to the webhook URL."""
        pass
