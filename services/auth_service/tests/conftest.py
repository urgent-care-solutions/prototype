import asyncio
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_app():
    from contextlib import asynccontextmanager

    from fastapi import FastAPI

    from app.api.v1.endpoints import auth, health
    from app.config import settings

    @asynccontextmanager
    async def test_lifespan(app: FastAPI):
        yield

    app = FastAPI(
        title=settings.PROJECT_NAME, version=settings.VERSION, lifespan=test_lifespan
    )

    @app.get("/")
    async def root():
        return {
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "running",
        }

    app.include_router(health.router, prefix=settings.API_V1_STR, tags=["health"])
    app.include_router(
        auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"]
    )

    return app


@pytest.fixture
async def client(test_app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_user_response():
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "organization_id": "660e8400-e29b-41d4-a716-446655440000",
        "role_id": "770e8400-e29b-41d4-a716-446655440000",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "is_provider": False,
        "provider_npi": None,
        "phone": None,
        "is_active": True,
        "last_login": None,
        "created_at": "2025-11-18T00:00:00",
        "updated_at": "2025-11-18T00:00:00",
    }
