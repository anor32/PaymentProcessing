import asyncio
import sys
from pathlib import Path

from src.application.usecases.process_payment import ProcessPaymentUseCase
from src.infrastructure.webhook.http_webhook_sender import HttpWebhookSender
from src.presentation.emulation_service.consumer_dependencies import (
    get_consumer_config,
    get_rabbit_broker,
    get_rabbit_consumer,
)
from src.presentation.emulation_service.topology import setup_topology

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


async def main() -> None:
    config = get_consumer_config()

    await setup_topology(config=config)

    broker = get_rabbit_broker()
    usecase = ProcessPaymentUseCase(
        webhook_sender=HttpWebhookSender(),
        max_retries=config.max_retries,
    )
    consumer = get_rabbit_consumer(broker=broker, usecase=usecase, config=config)

    await consumer.run()


if __name__ == "__main__":
    asyncio.run(main())
