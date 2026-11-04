FROM python:3.14-slim

WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем uv и завис
RUN pip install --no-cache-dir uv

# Копируем код проекта
COPY . .

# Устанавливаем production-зависимости (без dev)
RUN uv sync --frozen --no-dev

# Открытие порта
EXPOSE 8000

# Запуск приложения
CMD ["uv", "run", "uvicorn", "paymentprocessing:app", "--host", "0.0.0.0", "--port", "8000"]
