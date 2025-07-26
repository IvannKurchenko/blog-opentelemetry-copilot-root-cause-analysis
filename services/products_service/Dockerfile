FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl

ENV PYTHONUNBUFFERED=1 \
    OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true

WORKDIR /app

COPY pyproject.toml ./

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir . && \
    opentelemetry-bootstrap -a install

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && opentelemetry-instrument --service_name products-server uvicorn src.main:app --workers 1 --host 0.0.0.0 --port 8000"]