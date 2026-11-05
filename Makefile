SHELL := C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe
.SHELLFLAGS := -NoProfile -Command

list:
	Get-PSTree -Exclude .venv, .git, __pycache__, .idea, .ruff_cache

# Docker Compose команды
docker-start:
	docker compose up -d

docker-stop:
	docker compose down

docker-logs:
	docker compose logs -f

docker-build:
	docker compose build

docker-config:
	docker compose config

docker-down:
	docker compose down -v

# --- Локальный старт проекта (одной командой) ---

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

# Полный старт: инфраструктура -> миграции -> топология RabbitMQ -> API
start: db-up migrate setup
	uv run python bin/run_api.py

# --- Тестирование ---

# Запуск всех тестов
test:
	uv run pytest tests/

# Запуск тестов с подробным выводом
test-v:
	uv run pytest tests/ -v

# Запуск конкретного файла тестов
test-file:
	uv run pytest tests/$(FILE)