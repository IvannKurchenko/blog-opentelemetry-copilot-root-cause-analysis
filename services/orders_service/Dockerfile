FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml ./

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .

COPY . .
EXPOSE 8000

# Start the FastAPI server
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port 8000"]