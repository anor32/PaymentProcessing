SHELL := C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe
.SHELLFLAGS := -NoProfile -Command




# Поднять только инфраструктуру (PostgreSQL + RabbitMQ)
db-up:
	docker compose up -d postgres rabbitmq

# Применить миграции Alembic к БД
migrate:
	uv run alembic upgrade head

# Настроить топологию RabbitMQ (очереди, DLX, DLQ)
setup:
	uv run python bin/setup_rabbitmq.py

# Запустить только API-сервер
api:
	uv run python bin/run_api.py

# Запустить только Consumer (воркер RabbitMQ)
consumer:
	uv run python bin/run_consumer.py


start: db-up migrate setup
	uv run python bin/run_api.py


test:
	uv run pytest tests/



check:
	uv run mypy src/
	uv run ruff check src/ tests/
	uv run pytest tests/
