from fastapi import APIRouter
from app.schemas import HealthCheckResponse
from app.config import settings
from datetime import datetime
from tortoise import Tortoise

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    db_status = "connected"
    try:
        conn = Tortoise.get_connection("default")
        await conn.execute_query("SELECT 1")
    except Exception as e:
        db_status = f"error: {str(e)}"

    return HealthCheckResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        version=settings.VERSION,
        database=db_status,
        timestamp=datetime.utcnow(),
    )
