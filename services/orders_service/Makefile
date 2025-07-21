VENV := .venv
PIP := $(VENV)/bin/pip

#
# Setup: create a virtual environment, install dependencies etc.
#
.PHONY: venv
venv:
	@echo "Creating virtual environment..."
	@python -m venv $(VENV)
	@echo "Virtual environment created at $(VENV)"

activate:
	(source .venv/bin/activate)

install-dependencies: activate
	@echo "Installing dependencies..."
	@pip install .
	@pip install -e ".[dev]"
	@opentelemetry-bootstrap -a install

setup: venv install-dependencies

#
# Lint: run code quality checks
#
black: activate
	@echo "Running black..."
	black .

ruff: activate
	@echo "Running ruff..."
	ruff check .

mypy: activate
	@echo "Running mypy..."
	mypy --config-file pyproject.toml

lint: black ruff mypy

#
# Run: start the application and its dependencies
#
run-environment:
	docker compose up -d

run-application:
	export OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true && \
	export OTEL_LOG_LEVEL="debug"  && \
	opentelemetry-instrument \
		--traces_exporter console \
		--metrics_exporter console \
		--logs_exporter console \
		--service_name orders-server \
		uvicorn src.main:app --workers 1 --host 0.0.0.0 --port 8000 --reload

run: run-environment run-application

#
# Build: build the Docker image for the service
#
.PHONY: build

build:
	docker build -t orders-service .