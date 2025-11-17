from fastapi import APIRouter, status
from datetime import datetime, timezone

from app.config import settings
from app.schemas import HealthCheckResponse
from app.services.redis_token_manager import token_manager
from app.db.database import db_pool

router = APIRouter()


@router.get(
    "/health", response_model=HealthCheckResponse, status_code=status.HTTP_200_OK
)
async def health_check():
    db_status = "connected"
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
    except Exception:
        db_status = "disconnected"

    redis_status = "connected"
    try:
        await token_manager.redis_client.ping()
    except Exception:
        redis_status = "disconnected"

    return HealthCheckResponse(
        status="healthy"
        if db_status == "connected" and redis_status == "connected"
        else "degraded",
        timestamp=datetime.now(timezone.utc),
        version=settings.VERSION,
        database=db_status,
        redis=redis_status,
    )
