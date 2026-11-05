import asyncio
import logging
from typing import Any, cast

from faststream.rabbit import RabbitBroker, RabbitQueue

from src.presentation.emulation_service.config import ConsumerConfig

logger = logging.getLogger(__name__)


async def setup_topology(config: ConsumerConfig | None = None) -> None:
    if config is None:
        config = ConsumerConfig()

    broker = RabbitBroker(config.rabbitmq_url)
    await broker.start()

    try:
        await broker.declare_queue(RabbitQueue(config.dlq_name, durable=True))
        logger.info("Created DLQ %s", config.dlq_name)

        for queue_name, ttl in config.retry_queue_with_ttl:
            await broker.declare_queue(
                RabbitQueue(
                    queue_name,
                    durable=True,
                    arguments={
                        "x-message-ttl": ttl,
                        "x-dead-letter-exchange": "",
                        "x-dead-letter-routing-key": config.queue_name,
                    },
                )
            )
            logger.info("Created retry queue %s (ttl=%sms)", queue_name, ttl)

        await broker.declare_queue(
            RabbitQueue(
                config.queue_name,
                durable=True,
                arguments=cast(Any, config.main_queue_arguments),
            )
        )
        logger.info("Created main queue %s", config.queue_name)

        logger.info("RabbitMQ topology setup completed")
    finally:
        await broker.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(setup_topology())
