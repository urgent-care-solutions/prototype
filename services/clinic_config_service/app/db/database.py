from tortoise import Tortoise
from app.config import settings
import logging

logger = logging.getLogger(__name__)

TORTOISE_ORM = {
    "connections": {"default": settings.DATABASE_URL},
    "apps": {
        "models": {
            "models": ["app.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}


async def init_db():
    logger.info(f"Initializing database connection to {settings.DATABASE_URL}")
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.models"]},
    )
    await Tortoise.generate_schemas()
    logger.info("Database initialized successfully")


async def close_db():
    logger.info("Closing database connections")
    await Tortoise.close_connections()
    logger.info("Database connections closed")
