VENV := .venv
PIP := $(VENV)/bin/pip

#
# Setup: create a virtual environment, install dependencies etc.
#
.PHONY: venv
venv:
	@echo "Creating virtual environment..."
	@python -m venv $(VENV)

install-dependencies:
	@echo "Installing dependencies..."
	@pip install .
	@pip install -e ".[dev]"
	@opentelemetry-bootstrap -a install

setup: venv install-dependencies

#
# Lint: run code quality checks
#
black:
	@echo "Running black..."
	black .

ruff:
	@echo "Running ruff..."
	ruff check .

mypy:
	@echo "Running mypy..."
	mypy --config-file pyproject.toml

lint: black ruff mypy

#
# Run: start the application and its dependencies
#
run-environment:
	docker compose up -d

migrate:
	export MIGRATE_DATABASE_URL=postgresql://user:password@localhost:5432/products && \
	alembic upgrade head

run-application:
	export OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true && \
	export OTEL_LOG_LEVEL="debug"  && \
	opentelemetry-instrument \
		--traces_exporter console \
		--metrics_exporter console \
		--logs_exporter console \
		--service_name products-server \
		uvicorn src.main:app --workers 1 --host 0.0.0.0 --port 8000 --reload

run: run-environment migrate run-application

#
# Build: build the Docker image for the service
#
.PHONY: build

build:
	@echo "Building Docker image..."
	@docker build -t products-service .


run-build:
	@echo "Running built Docker container with dependencies..."
	@docker-compose -f all-docker-compose.yml up