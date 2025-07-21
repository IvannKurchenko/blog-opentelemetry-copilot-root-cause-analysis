"""
Orders Service Application Entry Point.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic_settings import BaseSettings
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware


class Settings(BaseSettings):
    """Environment settings for Orders Service."""
    redis_url: str = "redis://localhost:6379/0"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "orders"
    service_name: str = "orders-service"

    class Config:
        env_file = ".env"


settings = Settings()

# Enable OpenTelemetry auto-instrumentation manually because of the instrumentation issues.
# Please see for more details:
# https://github.com/open-telemetry/opentelemetry-python/issues/3477#issuecomment-1915743854
@asynccontextmanager
async def lifespan(app: FastAPI):
    import os, sys  # noqa: E401

    if "PYTHONPATH" not in os.environ:
        os.environ["PYTHONPATH"] = ":".join(sys.path)
    import opentelemetry.instrumentation.auto_instrumentation.sitecustomize  # noqa: F401

    yield

app = FastAPI(title=settings.service_name, lifespan=lifespan)


@app.on_event("startup")
async def startup_event():
    """Initialize connections to Redis and Kafka on startup."""
    # Redis client (async)
    import redis.asyncio as aioredis

    app.state.redis = aioredis.from_url(settings.redis_url)

    # Kafka producer (async)
    from aiokafka import AIOKafkaProducer

    app.state.kafka_producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
    )
    await app.state.kafka_producer.start()

    # Ensure Kafka topic exists
    from aiokafka.admin import AIOKafkaAdminClient, NewTopic
    admin_client = AIOKafkaAdminClient(
        bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
    )
    await admin_client.start()
    try:
        new_topic = NewTopic(
            name=settings.kafka_topic,
            num_partitions=1,
            replication_factor=1,
        )
        result = await admin_client.create_topics([new_topic])
        # result is a dict of topic -> exception for failures
        if result:
            for topic_name, error in result.items():
                if error:
                    logging.error(f"Failed to create topic {topic_name}: {error}")
    except Exception as exc:
        logging.error(f"Could not create topic {settings.kafka_topic}: {exc}")
    finally:
        await admin_client.close()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup connections on shutdown."""
    # Shutdown Kafka producer
    await app.state.kafka_producer.stop()

    # Close Redis connection
    await app.state.redis.close()


# Enable OpenTelemetry middleware for instrumentation
app = OpenTelemetryMiddleware(app)  # type: ignore

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)