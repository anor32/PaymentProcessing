FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv


COPY . .


RUN uv sync --no-dev


EXPOSE 8000

CMD ["sh", "-c", "uv run alembic upgrade head && uv run python bin/run_api.py"]
