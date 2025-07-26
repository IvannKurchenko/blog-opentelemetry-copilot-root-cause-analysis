run-observability:
	@docker-compose \
		-f docker-compose.observability.yaml \
		up

run-all:
	@docker-compose \
		-f docker-compose.app.yaml \
		-f docker-compose.observability.yaml \
		-f docker-compose.communication.yaml \
		up
