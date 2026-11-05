import asyncio
import logging

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.config import settings
from src.infrastructure.webhook.http_webhook_sender import HttpWebhookSender
from src.presentation.consumer import QUEUE_NAME, RabbitConsumer

logger = logging.getLogger(__name__)


async def main() -> None:
    engine = create_async_engine(settings.POSTGRES_CONNECTION_STRING)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    webhook_sender = HttpWebhookSender()

    consumer = RabbitConsumer(
        rabbitmq_url=settings.rabbitmq_url,
        queue_name=QUEUE_NAME,
        session_factory=session_factory,
        webhook_sender=webhook_sender,
    )

    try:
        await consumer.consume()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
