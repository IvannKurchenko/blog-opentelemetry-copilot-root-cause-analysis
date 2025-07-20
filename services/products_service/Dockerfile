FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    DATABASE_URL=postgresql+asyncpg://user:password@db:5432/database

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000"]