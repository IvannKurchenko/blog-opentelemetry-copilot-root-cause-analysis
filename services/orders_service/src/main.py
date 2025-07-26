"""
Orders Service Application Entry Point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic_settings import BaseSettings
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware

from fastapi import HTTPException, status, Path
from pydantic import BaseModel
import httpx
import uuid
import json

import redis.asyncio as aioredis
from aiokafka import AIOKafkaProducer


class Settings(BaseSettings):
    """Environment settings for Orders Service."""

    redis_url: str = "redis://localhost:6379/0"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "orders"
    service_name: str = "orders-service"
    product_service_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"


class OrderItem(BaseModel):
    product_id: int
    quantity: int


class Order(BaseModel):
    id: str
    user_id: int
    items: list[OrderItem]
    status: str


class CreateOrderRequest(BaseModel):
    user_id: int
    items: list[OrderItem]


class UpdateOrderStatusRequest(BaseModel):
    status: str


settings = Settings()


# Enable OpenTelemetry auto-instrumentation manually because of the instrumentation issues.
# Please see for more details:
# https://github.com/open-telemetry/opentelemetry-python/issues/3477#issuecomment-1915743854
@asynccontextmanager
async def lifespan(app: FastAPI):
    import os  # noqa: E401
    import sys  # noqa: E401

    if "PYTHONPATH" not in os.environ:
        os.environ["PYTHONPATH"] = ":".join(sys.path)
    import opentelemetry.instrumentation.auto_instrumentation.sitecustomize  # noqa: F401

    yield


app = FastAPI(title=settings.service_name, lifespan=lifespan)
redis = aioredis.from_url(settings.redis_url)
kafka_producer = AIOKafkaProducer(
    bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
)

# Startup logic moved to the lifespan context manager.

@asynccontextmanager
async def lifespan(app: FastAPI):
    import os, sys  # noqa: E401

    if "PYTHONPATH" not in os.environ:
        os.environ["PYTHONPATH"] = ":".join(sys.path)
    import opentelemetry.instrumentation.auto_instrumentation.sitecustomize  # noqa: F401

    # Initialize Kafka producer
    await kafka_producer.start()

    # Ensure a Kafka topic exists
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


# Removed the deprecated @app.on_event("shutdown") logic as it is now handled in the lifespan context manager.


async def validate_products(items: list[OrderItem]) -> None:
    """Ensure all product IDs exist in the products service."""
    async with httpx.AsyncClient() as client:
        for item in items:
            resp = await client.get(
                f"{settings.product_service_url}/products/{item.product_id}"
            )
            if resp.status_code != status.HTTP_200_OK:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product {item.product_id} not found",
                )


async def publish_event(event_type: str, order: dict) -> None:
    """Publish an order event to Kafka."""
    message = {"event": event_type, "order": order}
    await kafka_producer.send_and_wait(
        settings.kafka_topic,
        json.dumps(message).encode(),
    )


@app.get("/orders", response_model=list[Order])
async def list_orders() -> list[Order]:
    """Retrieve all orders."""
    keys = await redis.keys("order:*")
    orders: list[Order] = []
    for key in keys:
        raw = await redis.get(key)
        if raw:
            orders.append(Order(**json.loads(raw)))
    return orders


@app.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: str = Path(..., description="Order ID")) -> Order:
    """Retrieve a specific order by ID."""
    raw = await redis.get(f"order:{order_id}")
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    return Order(**json.loads(raw))


@app.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(request: CreateOrderRequest) -> Order:
    """Create a new order after validating products."""
    await validate_products(request.items)
    order_id = str(uuid.uuid4())
    order = {
        "id": order_id,
        "user_id": request.user_id,
        "items": [item.model_dump() for item in request.items],
        "status": "pending",
    }
    await redis.set(f"order:{order_id}", json.dumps(order))
    await publish_event("order_created", order)
    return Order(**order)


@app.put("/orders/{order_id}", response_model=Order)
async def update_order(
    order_id: str = Path(..., description="Order ID"),
    request: UpdateOrderStatusRequest = None,
) -> Order:
    """Update the status of an existing order."""
    raw = await redis.get(f"order:{order_id}")
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    order = json.loads(raw)
    order["status"] = request.status
    await redis.set(f"order:{order_id}", json.dumps(order))
    await publish_event("order_updated", order)
    return Order(**order)


@app.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(order_id: str = Path(..., description="Order ID")) -> None:
    """Delete an order by ID."""
    key = f"order:{order_id}"
    exists = await redis.exists(key)
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    raw = await redis.get(key)
    order = json.loads(raw) if raw else {}
    await redis.delete(key)
    await publish_event("order_deleted", order)

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": settings.service_name}

# Enable OpenTelemetry middleware for instrumentation
app = OpenTelemetryMiddleware(app)  # type: ignore

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
