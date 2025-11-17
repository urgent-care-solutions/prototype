from fastapi import APIRouter, status
from datetime import datetime, timezone
from tortoise import Tortoise

from app.config import settings
from app.schemas import HealthCheckResponse
from app.services.auth_service import auth_service

router = APIRouter()


@router.get(
    "/health", response_model=HealthCheckResponse, status_code=status.HTTP_200_OK
)
async def health_check():
    db_status = "connected"
    try:
        conn = Tortoise.get_connection("default")
        await conn.execute_query("SELECT 1")
    except Exception:
        db_status = "disconnected"

    redis_status = "connected" if auth_service.redis_client else "disabled"
    if auth_service.redis_client:
        try:
            await auth_service.redis_client.ping()
        except Exception:
            redis_status = "disconnected"

    return HealthCheckResponse(
        status="healthy" if db_status == "connected" else "degraded",
        timestamp=datetime.now(timezone.utc),
        version=settings.VERSION,
        database=db_status,
        redis=redis_status,
    )
