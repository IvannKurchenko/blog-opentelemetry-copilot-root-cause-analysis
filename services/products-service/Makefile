VENV := .venv
PIP := $(VENV)/bin/pip

#
# Setup: create a virtual environment, install dependencies etc.
#
.PHONY: venv
venv:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)

install-dependencies:
	@echo "Installing dependencies..."
	@pip install .
	@opentelemetry-bootstrap -a install

setup: venv install-dependencies

run-environment:
	docker compose up -d

migrate:
	export DATABASE_URL=postgresql://user:password@localhost:5432/database && \
	alembic upgrade head

run-application:
	export OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true && \
	export OTEL_LOG_LEVEL="debug"  && \
	opentelemetry-instrument \
		--traces_exporter console \
		--metrics_exporter console \
		--logs_exporter console \
		--service_name products-server \
		uvicorn main:app --workers 1 --host 0.0.0.0 --port 8000 --reload

run: run-environment migrate run-application

build:
	docker build -t products-service .