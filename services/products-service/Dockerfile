FROM python:3.12-slim

# Ensure stdout/stderr are unbuffered and set default database URL
ENV PYTHONUNBUFFERED=1 \
    DATABASE_URL=postgresql+asyncpg://user:password@db:5432/database

# Set working directory
WORKDIR /app

# Copy project metadata for dependency resolution
COPY pyproject.toml uv.lock ./

# Install build tools and project dependencies from pyproject.toml
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .

# Copy application code
COPY . .

# Expose the application port
EXPOSE 8000

# Run database migrations then start the FastAPI server
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]