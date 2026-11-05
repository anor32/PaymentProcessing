from pydantic import BaseModel


class ConsumerConfig(BaseModel):
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672//"
    queue_name: str = "payments.new"
    dlq_name: str = "payments.dlq"
    max_retries: int = 3
    retry_queues: tuple[str, ...] = ("payments.retry.1", "payments.retry.2", "payments.retry.3")
    retry_ttls: dict[str, int] = {
        "payments.retry.1": 1000,
        "payments.retry.2": 2000,
        "payments.retry.3": 4000,
    }
    retry_backoff_base: float = 2.0
    retry_backoff_max_delay: float = 30.0
    retry_initial_delay: float = 1.0

    model_config = {"frozen": True}

    @property
    def retry_queue_with_ttl(self) -> list[tuple[str, int]]:
        return [
            (queue_name, self.retry_ttls.get(queue_name, 1000)) for queue_name in self.retry_queues
        ]

    @property
    def main_queue_arguments(self) -> dict[str, str]:
        return {
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": self.dlq_name,
        }

    def retry_delay_seconds(self, retry_count: int) -> float:
        attempt = max(retry_count, 1)
        delay: float = self.retry_initial_delay * (self.retry_backoff_base ** (attempt - 1))
        return min(delay, self.retry_backoff_max_delay)
