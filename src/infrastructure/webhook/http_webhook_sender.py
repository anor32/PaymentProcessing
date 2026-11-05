import logging
from typing import Any

import httpx

from src.domain.interfaces.webhook_sender import IWebhookSender

logger = logging.getLogger(__name__)


class HttpWebhookSender(IWebhookSender):
    def __init__(self, timeout: float = 10.0) -> None:
        self._timeout = timeout

    async def send(self, url: str, payload: dict[str, Any]) -> None:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            logger.info("Webhook delivered to %s (status=%s)", url, response.status_code)
