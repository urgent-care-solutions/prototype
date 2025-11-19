from datetime import datetime

from fastapi import APIRouter

from app.config import settings
from app.core.redis import redis_client

router = APIRouter()


@router.get("/health")
async def health_check():
    redis_status = "connected"
    try:
        if redis_client.client:
            redis_client.client.ping()
        else:
            redis_status = "not configured"
    except Exception as e:
        redis_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "version": settings.VERSION,
        "redis": redis_status,
        "timestamp": datetime.utcnow().isoformat(),
    }
