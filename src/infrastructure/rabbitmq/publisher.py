import logging
from typing import Any

from faststream.rabbit import RabbitBroker

from src.domain.interfaces.message_publisher import IMessagePublisher

logger = logging.getLogger(__name__)


class RabbitMQPublisher(IMessagePublisher):
    """Adapter for publishing messages to RabbitMQ (persistent delivery mode)."""

    def __init__(self, url: str) -> None:
        self._url = url
        self._broker: RabbitBroker | None = None

    async def start(self) -> None:
        """Opens connection to the broker."""
        self._broker = RabbitBroker(self._url)
        await self._broker.start()
        logger.info("RabbitMQPublisher started")

    async def stop(self) -> None:
        """Closes connection to the broker."""
        if self._broker is not None:
            await self._broker.stop()
            self._broker = None
            logger.info("RabbitMQPublisher stopped")

    async def publish(self, message: dict[str, Any], queue_name: str) -> None:
        """Publishes a message to the queue (persistent delivery mode)."""
        if self._broker is None:
            raise RuntimeError("RabbitMQPublisher is not started")
        await self._broker.publish(message, queue=queue_name)
        logger.debug("Published to %s: %s", queue_name, message)
