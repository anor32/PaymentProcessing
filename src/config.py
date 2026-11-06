import re

from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    POSTGRES_CONNECTION_STRING: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5434/payment_processing"
    )

    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    API_KEY: str = "secret-api-key"

    @field_validator("POSTGRES_CONNECTION_STRING", mode="before")
    @classmethod
    def ensure_asyncpg_driver(cls, v: str) -> str:
        if v.startswith(("postgres://", "postgresql://")):
            v = re.sub(r"^postgres(?:ql)?://", "postgresql+asyncpg://", v)
        return v

    @computed_field
    def rabbitmq_url(self) -> str:
        vhost = self.RABBITMQ_VHOST
        if vhost == "/":
            vhost = "%2F"

        return (
            f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}"
            f"@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{vhost}"
        )


settings = Settings()
