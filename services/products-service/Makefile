venv:
	uv venv

lint:
	uv run ruff check

prepare-environment:
	docker compose up -d

migrate:
	export DATABASE_URL=postgresql://user:password@localhost:5432/database && \
	uv run alembic upgrade head

run-service:
	uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

run: prepare-environment migrate run-service

lock:
	uv lock

sync:
	uv sync

 