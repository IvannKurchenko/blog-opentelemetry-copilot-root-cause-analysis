import logging
import os
from contextlib import asynccontextmanager
from typing import Optional, List, AsyncGenerator

from fastapi import FastAPI, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, Float, select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost:5432/products",
)

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore
Base = declarative_base()


class Product(Base):  # type: ignore
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)


class ProductCreate(BaseModel):  # Pydantic schema for input
    name: str
    description: Optional[str] = None
    price: float
    stock: int


class ProductRead(ProductCreate):  # Pydantic schema for output
    id: int

    class Config:
        orm_mode = True


class ProductList(BaseModel):
    items: List[ProductRead]
    total: int
    page: int
    page_size: int


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None


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


app = FastAPI(title="Products Service", lifespan=lifespan)


@app.on_event("startup")
async def on_startup():
    """Initialize database: create tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency: Async database session."""
    async with AsyncSessionLocal() as session:
        yield session


@app.post("/products", response_model=ProductRead)
async def create_product(
    product: ProductCreate, session: AsyncSession = Depends(get_session)
):
    """Create a new product in the database."""
    db_product = Product(**product.dict())
    session.add(db_product)
    await session.commit()
    await session.refresh(db_product)
    return db_product


@app.get("/products/{product_id}", response_model=ProductRead)
async def get_product(product_id: int, session: AsyncSession = Depends(get_session)):
    """Retrieve a product by its ID."""
    product = await session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/products", response_model=ProductList)
async def search_products(
    name: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_stock: Optional[int] = None,
    max_stock: Optional[int] = None,
    page: int = 1,
    page_size: int = 10,
    session: AsyncSession = Depends(get_session),
):
    """Search products by filters with pagination."""
    filters = []
    if name:
        filters.append(Product.name.ilike(f"%{name}%"))
    if min_price is not None:
        filters.append(Product.price >= min_price)  # type: ignore
    if max_price is not None:
        filters.append(Product.price <= max_price)  # type: ignore
    if min_stock is not None:
        filters.append(Product.stock >= min_stock)  # type: ignore
    if max_stock is not None:
        filters.append(Product.stock <= max_stock)  # type: ignore

    count_stmt = select(func.count()).select_from(Product)
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = select(Product)
    if filters:
        stmt = stmt.where(*filters)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    products = await session.execute(stmt)
    result = list(ProductRead(**dict(product)) for product in products.scalars().all())
    return ProductList(items=result, total=total, page=page, page_size=page_size)


@app.patch("/products/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    product: ProductUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a product's fields by its ID."""
    db_product = await session.get(Product, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    update_data = product.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
    session.add(db_product)
    await session.commit()
    await session.refresh(db_product)
    return db_product


@app.delete("/products/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Delete a product by its ID."""
    db_product = await session.get(Product, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    await session.delete(db_product)
    await session.commit()
    return Response(status_code=204)


# Enable OpenTelemetry middleware for instrumentation
app = OpenTelemetryMiddleware(app)  # type: ignore

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
