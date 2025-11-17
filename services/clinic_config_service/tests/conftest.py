# tests/conftest.py
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from tortoise import Tortoise
from fastapi import FastAPI
from contextlib import asynccontextmanager


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def initialize_tests():
    """Initialize Tortoise ORM once for all tests."""
    # Initialize Tortoise with in-memory SQLite
    await Tortoise.init(db_url="sqlite://:memory:", modules={"models": ["app.models"]})

    # Generate schemas
    await Tortoise.generate_schemas()

    yield

    # Cleanup
    await Tortoise.close_connections()


@pytest.fixture
def test_app():
    """Create test FastAPI app without Tortoise init in lifespan."""
    from app.config import settings
    from app.api.v1.endpoints import users, roles, clinics, health, organizations

    @asynccontextmanager
    async def test_lifespan(app: FastAPI):
        yield  # Skip Tortoise init - already done by fixture

    app = FastAPI(
        title=settings.PROJECT_NAME, version=settings.VERSION, lifespan=test_lifespan
    )

    # Register all routers
    app.include_router(health.router, prefix=settings.API_V1_STR, tags=["health"])
    app.include_router(
        organizations.router, prefix=settings.API_V1_STR, tags=["organizations"]
    )
    app.include_router(roles.router, prefix=settings.API_V1_STR, tags=["roles"])
    app.include_router(users.router, prefix=settings.API_V1_STR, tags=["users"])
    app.include_router(clinics.router, prefix=settings.API_V1_STR, tags=["clinics"])

    @app.get("/")
    async def root():
        return {
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "running",
        }

    return app


@pytest.fixture
async def client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Create test client for the test app."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
