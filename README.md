# Payment Processing Service

Асинхронный сервис процессинга платежей (тестовое задание). Принимает платежи, эмулирует обработку через внешний шлюз и уведомляет клиента через webhook.

## Стек

- FastAPI + Pydantic v2 — API
- SQLAlchemy 2.0 (async) + PostgreSQL — БД
- RabbitMQ (FastStream) — брокер сообщений
- Alembic — миграции
- Docker + docker-compose

## Архитектура

Чистая многослойная архитектура, зависимости направлены внутрь:

```
presentation → application → domain
              ↑              ↓
              └── infrastructure
```

- **domain** — сущности, value objects, исключения, интерфейсы (без внешних библиотек)
- **application** — use cases (создание/получение/обработка платежа, outbox)
- **infrastructure** — SQLAlchemy-модели, репозитории, UoW, RabbitMQ publisher, HTTP webhook sender
- **presentation** — FastAPI роуты, Pydantic-схемы, зависимости, consumer

## Схема работы

1. `POST /api/v1/payments` — создаёт платеж со статусом `pending`, сохраняет событие в outbox (одна транзакция), возвращает `202 Accepted`
2. `OutboxPublisherWorker` читает события из outbox и публикует в очередь RabbitMQ `payments.new`
3. `RabbitConsumer` забирает сообщение, эмулирует обработку (2–5 сек, 90% успех / 10% ошибка), обновляет статус в БД, отправляет webhook
4. При ошибке webhook — ретраи с экспоненциальной задержкой, затем DLQ (`payments.dlq`)
5. `GET /api/v1/payments/{id}` — возвращает информацию о платеже

## Требования и подготовка

### Системные требования
- Python 3.14+
- Docker + Docker Compose

### Установка зависимостей проекта

Проект использует [uv](https://docs.astral.sh/uv/) для управления зависимостями:

```bash
# Установите uv (если ещё не установлено)
# macOS/Linux:
#   curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows:
#   python -m pip install uv

# Установка всех зависимостей проекта и инструментов разработки
uv sync
```

### Настройка окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

### Подъём инфраструктуры (Docker)

Поднимите PostgreSQL и RabbitMQ:

```bash
docker compose up -d postgres rabbitmq
```

Примените миграции БД:

```bash
uv run alembic upgrade head
```

Настройте топологию RabbitMQ (очереди, DLX, DLQ):

```bash
# Файл bin/setup_rabbitmq.py создаст необходимые очереди и обменник
# Если файл отсутствует, можно настроить вручную через RabbitMQ UI или скрипт
```

### Запуск сервиса

Запустите API-сервер:

```bash
uv run python bin/run_api.py
```

Или запустите весь сервис (API + Consumer):

```bash
make start
```


API доступен на `http://localhost:8000`, RabbitMQ UI — `http://localhost:15672` (guest/guest).

## Make команды

Доступные задачи из [`Makefile`](Makefile):

| Команда | Описание |
|---------|----------|
| `make db-up` | Поднять PostgreSQL и RabbitMQ (Docker) |
| `make migrate` | Применить миграции Alembic к БД |
| `make setup` | Настроить топологию RabbitMQ (очереди, DLX, DLQ) |
| `make api` | Запустить только API-сервер |
| `make consumer` | Запустить только Consumer (воркер RabbitMQ) |
| `make start` | Полная сборка: инфраструктура + миграции + топология + запуск API и Consumer'а |
| `make test` | Запуск тестов через pytest |
| `make check` | Проверка кода: mypy, ruff, pytest |

Примеры использования:

```bash
# Только проверка кода
make check

# Полная сборка и запуск
make start

# Раздельный запуск (для разработки)
make db-up
make migrate
make setup
make api    # в одной терминале
make consumer    # в другой терминале
```

## API

- `POST /api/v1/payments` — создание платежа (заголовки: `X-API-Key`, `Idempotency-Key`)
- `GET /api/v1/payments/{id}` — получение платежа
- `GET /health` — проверка работоспособности

## Переменные окружения

См. `.env.example`: `POSTGRES_CONNECTION_STRING`, `API_KEY`, настройки RabbitMQ.
