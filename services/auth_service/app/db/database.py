from tortoise import Tortoise
from app.config import settings
import logging

logger = logging.getLogger(__name__)

TORTOISE_ORM = {
    "connections": {"default": settings.DATABASE_URL},
    "apps": {
        "models": {
            "models": ["app.models"],
            "default_connection": "default",
        },
    },
}


async def init_db():
    try:
        await Tortoise.init(config=TORTOISE_ORM)
        await Tortoise.generate_schemas()
        logger.info("Auth service connected to clinic database")
    except Exception as e:
        logger.error(f"Database init failed: {e}")
        raise


async def close_db():
    try:
        await Tortoise.close_connections()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Database close failed: {e}")
        raise
